from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request, Response, status
from jwt.exceptions import InvalidTokenError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import AdminUser, ApiClient

settings = get_settings()
password_hash = PasswordHasher()

ADMIN_COOKIE = 'solarlead_admin'
CSRF_COOKIE = 'solarlead_csrf'


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return password_hash.verify(hashed, password)
    except VerifyMismatchError:
        return False


def create_access_token(user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user_id),
        'email': email,
        'iat': now,
        'exp': now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def set_auth_cookies(response: Response, token: str) -> str:
    csrf = secrets.token_urlsafe(24)
    common = dict(
        secure=settings.cookie_secure,
        samesite='lax',
        domain=settings.cookie_domain or None,
        path='/',
        max_age=settings.access_token_minutes * 60,
    )
    response.set_cookie(ADMIN_COOKIE, token, httponly=True, **common)
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, **common)
    return csrf


def clear_auth_cookies(response: Response):
    response.delete_cookie(ADMIN_COOKIE, domain=settings.cookie_domain or None, path='/')
    response.delete_cookie(CSRF_COOKIE, domain=settings.cookie_domain or None, path='/')


def get_current_admin(
    token: Annotated[str | None, Cookie(alias=ADMIN_COOKIE)] = None,
    db: Session = Depends(get_db),
) -> AdminUser:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Nicht angemeldet')
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get('sub', '0'))
    except (InvalidTokenError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Session ungültig')
    user = db.get(AdminUser, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Benutzer nicht aktiv')
    return user


def require_csrf(
    request: Request,
    x_csrf_token: Annotated[str | None, Header(alias='X-CSRF-Token')] = None,
    csrf_cookie: Annotated[str | None, Cookie(alias=CSRF_COOKIE)] = None,
):
    if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        if not x_csrf_token or not csrf_cookie or not hmac.compare_digest(x_csrf_token, csrf_cookie):
            raise HTTPException(status_code=403, detail='CSRF-Prüfung fehlgeschlagen')


def api_key_hash(raw_key: str) -> str:
    return hashlib.sha256(f'{settings.api_key_salt}:{raw_key}'.encode()).hexdigest()


def require_api_client(
    x_api_key: Annotated[str | None, Header(alias='X-API-Key')] = None,
    db: Session = Depends(get_db),
) -> ApiClient:
    if not x_api_key:
        raise HTTPException(status_code=401, detail='API-Key fehlt')
    key_hash = api_key_hash(x_api_key)
    client = db.query(ApiClient).filter(ApiClient.key_hash == key_hash, ApiClient.is_active.is_(True)).first()
    if not client:
        raise HTTPException(status_code=401, detail='API-Key ungültig')
    return client
