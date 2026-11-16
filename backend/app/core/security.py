from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError


ALGORITHM = "HS256"


def has_valid_signing_key(secret_key: str | None) -> bool:
    return bool(secret_key and len(secret_key.encode("utf-8")) >= 32)


def create_teacher_token(secret_key: str, expire_hours: int = 8) -> tuple[str, int]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=expire_hours)
    payload = {"sub": "teacher", "role": "teacher", "iat": now, "exp": expires_at}
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM), expire_hours * 60 * 60


def decode_teacher_token(token: str, secret_key: str) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        secret_key,
        algorithms=[ALGORITHM],
        options={"require": ["sub", "role", "exp"]},
    )
    if payload.get("sub") != "teacher" or payload.get("role") != "teacher":
        raise InvalidTokenError("Invalid teacher claims")
    return payload
