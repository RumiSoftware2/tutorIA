import secrets

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.core.security import create_teacher_token, has_valid_signing_key
from app.schemas.auth import TeacherLoginRequest, TeacherLoginResponse

router = APIRouter(prefix="/auth/teacher", tags=["auth"])


@router.post("/login", response_model=TeacherLoginResponse)
def teacher_login(
    request: TeacherLoginRequest,
    settings: Settings = Depends(get_settings),
) -> TeacherLoginResponse:
    if not settings.teacher_access_code or not has_valid_signing_key(settings.jwt_secret_key):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El acceso docente no está configurado en el servidor.",
        )
    if not secrets.compare_digest(
        request.access_code.encode("utf-8"), settings.teacher_access_code.encode("utf-8")
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Clave docente no válida.")

    token, expires_in = create_teacher_token(settings.jwt_secret_key, settings.jwt_expire_hours)
    return TeacherLoginResponse(access_token=token, expires_in=expires_in)
