from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.auth import get_current_admin
from ...core.config import settings
from ...core.security import create_access_token, verify_password
from ...schemas.auth import AdminInfo, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    if not settings.ADMIN_PASSWORD_HASH or not settings.JWT_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="auth_not_configured",
        )
    valid_user = data.username == settings.ADMIN_USERNAME
    valid_pwd = verify_password(data.password, settings.ADMIN_PASSWORD_HASH)
    if not (valid_user and valid_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials",
        )
    token, expires_in = create_access_token(subject=data.username)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=AdminInfo)
def me(username: str = Depends(get_current_admin)):
    return AdminInfo(username=username)
