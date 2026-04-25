import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import cast

import jwt

from app.core.config import settings


class TokenError(ValueError):
    pass


def issue_access_token(*, user_id: str, email: str, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRES_IN_SECONDS)).timestamp()),
    }
    secret = settings.EFFECTIVE_ACCESS_TOKEN_SECRET
    if not secret:
        raise TokenError("ACCESS_TOKEN_SECRET or JWT_SECRET must be configured")
    return cast(str, jwt.encode(payload, secret, algorithm="HS256"))


def decode_access_token(token: str) -> dict[str, str | int]:
    secret = settings.EFFECTIVE_ACCESS_TOKEN_SECRET
    if not secret:
        raise TokenError("ACCESS_TOKEN_SECRET or JWT_SECRET must be configured")
    try:
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid access token") from exc
    return cast(dict[str, str | int], decoded)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    pepper = settings.REFRESH_TOKEN_PEPPER
    if not pepper:
        raise TokenError("REFRESH_TOKEN_PEPPER must be configured")
    digest = hmac.new(pepper.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest


def refresh_expiry_utc() -> datetime:
    return datetime.now(UTC) + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRES_IN_SECONDS)
