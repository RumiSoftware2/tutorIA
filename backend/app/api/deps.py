from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError

from app.core.config import Settings, get_settings
from app.core.security import decode_teacher_token, has_valid_signing_key

bearer_scheme = HTTPBearer(auto_error=False)


def require_teacher(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> dict:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Se requiere una sesión docente válida.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or not has_valid_signing_key(settings.jwt_secret_key):
        raise unauthorized
    try:
        return decode_teacher_token(credentials.credentials, settings.jwt_secret_key)
    except InvalidTokenError:
        raise unauthorized from None
