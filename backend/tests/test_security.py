from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError

from app.api.routes.auth import teacher_login
from app.api.deps import require_teacher
from app.core.config import Settings
from app.core.security import create_teacher_token, decode_teacher_token
from app.schemas.auth import TeacherLoginRequest


def test_teacher_token_round_trip_and_wrong_secret_rejected() -> None:
    secret = "s" * 40
    token, expires_in = create_teacher_token(secret, expire_hours=8)

    assert expires_in == 8 * 60 * 60
    assert decode_teacher_token(token, secret)["role"] == "teacher"
    with pytest.raises(InvalidTokenError):
        decode_teacher_token(token, "x" * 40)


def test_expired_and_wrong_role_tokens_are_rejected() -> None:
    expired = jwt.encode(
        {"sub": "teacher", "role": "teacher", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        "s" * 40,
        algorithm="HS256",
    )
    wrong_role = jwt.encode(
        {"sub": "student", "role": "student", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "s" * 40,
        algorithm="HS256",
    )

    with pytest.raises(InvalidTokenError):
        decode_teacher_token(expired, "s" * 40)
    with pytest.raises(InvalidTokenError):
        decode_teacher_token(wrong_role, "s" * 40)


def test_teacher_login_issues_token_for_correct_code() -> None:
    secret = "s" * 40
    settings = Settings(teacher_access_code="docente-á", jwt_secret_key=secret, jwt_expire_hours=8)

    response = teacher_login(TeacherLoginRequest(access_code="docente-á"), settings)

    assert response.token_type == "bearer"
    assert decode_teacher_token(response.access_token, secret)["sub"] == "teacher"


def test_teacher_login_uses_generic_unauthorized_error_for_wrong_code() -> None:
    settings = Settings(teacher_access_code="docente-test", jwt_secret_key="s" * 40)

    with pytest.raises(HTTPException) as error:
        teacher_login(TeacherLoginRequest(access_code="wrong"), settings)

    assert error.value.status_code == 401
    assert error.value.detail == "Clave docente no válida."


def test_teacher_login_reports_missing_server_configuration() -> None:
    settings = Settings(teacher_access_code="docente-test", jwt_secret_key="too-short")

    with pytest.raises(HTTPException) as error:
        teacher_login(TeacherLoginRequest(access_code="docente-test"), settings)

    assert error.value.status_code == 503


def test_protected_dependency_accepts_only_a_valid_bearer_token() -> None:
    secret = "s" * 40
    settings = Settings(jwt_secret_key=secret)
    token, _ = create_teacher_token(secret)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    assert require_teacher(credentials, settings)["role"] == "teacher"

    with pytest.raises(HTTPException) as error:
        require_teacher(None, settings)
    assert error.value.status_code == 401

    with pytest.raises(HTTPException) as error:
        require_teacher(HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid"), settings)
    assert error.value.status_code == 401
