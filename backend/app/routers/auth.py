from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import AdminUser
from ..schemas import AdminMe, LoginRequest
from ..security import clear_auth_cookies, create_access_token, get_current_admin, require_csrf, set_auth_cookies, verify_password

router = APIRouter(prefix='/api/auth', tags=['auth'])

@router.post('/login', response_model=AdminMe)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(AdminUser).filter(AdminUser.email == email).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail='E-Mail oder Passwort falsch')
    token = create_access_token(user.id, user.email)
    set_auth_cookies(response, token)
    return user

@router.post('/logout', dependencies=[Depends(require_csrf)])
def logout(response: Response, user: AdminUser = Depends(get_current_admin)):
    clear_auth_cookies(response)
    return {'ok': True}

@router.get('/me', response_model=AdminMe)
def me(user: AdminUser = Depends(get_current_admin)):
    return user
