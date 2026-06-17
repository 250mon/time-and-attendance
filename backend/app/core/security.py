from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.core.config import settings

ACCESS_TOKEN_COOKIE = "access_token"
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(user_id: UUID) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": str(user_id), "exp": expire}
    token: str = jwt.encode(payload, settings.backend_secret_key, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> UUID:
    payload = jwt.decode(token, settings.backend_secret_key, algorithms=[ALGORITHM])
    return UUID(str(payload["sub"]))
