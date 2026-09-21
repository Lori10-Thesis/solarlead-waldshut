from fastapi import Request
from .config import get_settings

settings = get_settings()


def client_ip(request: Request) -> str | None:
    """Return the originating client IP.

    X-Forwarded-For is trusted only when explicitly enabled. In production the
    backend is not published directly and receives traffic through Caddy.
    """
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else None
