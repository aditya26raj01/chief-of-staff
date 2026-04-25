import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.parse import urlencode

import httpx
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crypto_utils import CryptoError, encrypt_secret
from app.auth.oauth_con_entity import OAuthConnection, OAuthProvider
from app.auth.refresh_token_entity import RefreshToken
from app.auth.token_utils import (
    TokenError,
    generate_refresh_token,
    hash_refresh_token,
    issue_access_token,
    refresh_expiry_utc,
)
from app.auth.user_entity import User, UserRole
from app.core.config import settings


class AuthServiceError(ValueError):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class AuthUserPayload:
    id: str
    email: str
    display_name: str
    avatar_url: str
    role: str


@dataclass
class AuthTokensPayload:
    access_token: str
    refresh_token: str


@dataclass
class AuthResult:
    user: AuthUserPayload
    tokens: AuthTokensPayload


def build_google_init_url() -> str:
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(settings.GOOGLE_OAUTH_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{base_url}?{urlencode(params)}"


async def _exchange_code(code: str) -> dict[str, str | int]:
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(token_url, data=payload)
    if response.status_code >= 400:
        raise AuthServiceError("Invalid Google authorization code", 401)
    body = response.json()
    if not isinstance(body, dict):
        raise AuthServiceError("Invalid Google token payload", 401)
    return cast(dict[str, str | int], body)


def _verify_google_id_token(id_token_raw: str) -> Mapping[str, object]:
    try:
        claims = cast(
            Mapping[str, object],
            id_token.verify_oauth2_token(
                id_token_raw,
                GoogleRequest(),
                settings.GOOGLE_CLIENT_ID,
            ),
        )
    except Exception as exc:  # pragma: no cover
        raise AuthServiceError("Invalid Google token", 401) from exc

    email = cast(Any, claims.get("email"))
    email_verified = cast(Any, claims.get("email_verified"))
    subject = cast(Any, claims.get("sub"))
    if not isinstance(email, str) or not email:
        raise AuthServiceError("Google account email missing", 401)
    if email_verified is not True:
        raise AuthServiceError("Google account email is not verified", 401)
    if not isinstance(subject, str) or not subject:
        raise AuthServiceError("Google subject missing", 401)
    return claims


async def _issue_local_tokens(
    *,
    db: AsyncSession,
    user: User,
    user_agent: str | None,
    ip_address: str | None,
    revoke_existing_id: uuid.UUID | None = None,
) -> AuthTokensPayload:
    if revoke_existing_id is not None:
        existing = await db.get(RefreshToken, revoke_existing_id)
        if existing is not None and existing.revoked_at is None:
            existing.revoked_at = datetime.now(UTC)

    refresh_token_plain = generate_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token_plain)
    refresh_record = RefreshToken(
        token_hash=refresh_hash,
        user_id=user.id,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=refresh_expiry_utc(),
        revoked_at=None,
    )
    db.add(refresh_record)

    access_token = issue_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.role.value,
    )

    return AuthTokensPayload(access_token=access_token, refresh_token=refresh_token_plain)


async def handle_google_callback(
    *,
    db: AsyncSession,
    code: str,
    user_agent: str | None,
    ip_address: str | None,
) -> AuthResult:
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise AuthServiceError("Google OAuth credentials are not configured", 500)

    token_data = await _exchange_code(code)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    raw_id_token = token_data.get("id_token")
    token_type = token_data.get("token_type")
    scope = token_data.get("scope")
    expires_in = token_data.get("expires_in")

    if not isinstance(raw_id_token, str) or not raw_id_token:
        raise AuthServiceError("Missing id_token from Google", 401)
    if not isinstance(access_token, str) or not access_token:
        raise AuthServiceError("Missing access_token from Google", 401)
    if not isinstance(refresh_token, str) or not refresh_token:
        raise AuthServiceError("Missing refresh_token from Google", 401)

    claims = _verify_google_id_token(raw_id_token)
    email = str(claims["email"]).lower().strip()
    sub = str(claims["sub"])  # provider account id
    display_name = str(claims.get("name") or email)
    avatar_url = str(claims.get("picture") or "")

    try:
        encrypted_access = encrypt_secret(access_token)
        encrypted_refresh = encrypt_secret(refresh_token)
    except CryptoError as exc:
        raise AuthServiceError(str(exc), 500) from exc

    access_exp = None
    if isinstance(expires_in, int):
        access_exp = datetime.now(UTC) + timedelta(seconds=expires_in)

    async with db.begin():
        user_result = await db.execute(select(User).where(User.email == email))
        user = user_result.scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                display_name=display_name,
                avatar_url=avatar_url,
                role=UserRole.USER,
            )
            db.add(user)
            await db.flush()
        else:
            user.display_name = display_name
            user.avatar_url = avatar_url

        conn_result = await db.execute(
            select(OAuthConnection).where(
                and_(
                    OAuthConnection.user_id == user.id,
                    OAuthConnection.provider == OAuthProvider.GOOGLE,
                )
            )
        )
        connection = conn_result.scalar_one_or_none()
        if connection is None:
            connection = OAuthConnection(
                user_id=user.id,
                provider=OAuthProvider.GOOGLE,
                provider_account_id=sub,
                provider_email=email,
            )
            db.add(connection)

        connection.provider_account_id = sub
        connection.provider_email = email
        connection.access_token_encrypted = encrypted_access
        connection.refresh_token_encrypted = encrypted_refresh
        connection.access_token_expires_at = access_exp
        connection.scope = scope if isinstance(scope, str) else None
        connection.token_type = token_type if isinstance(token_type, str) else None
        connection.revoked_at = None

        tokens = await _issue_local_tokens(
            db=db,
            user=user,
            user_agent=user_agent,
            ip_address=ip_address,
        )

    return AuthResult(
        user=AuthUserPayload(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            role=user.role.value,
        ),
        tokens=tokens,
    )


async def refresh_session(
    *,
    db: AsyncSession,
    refresh_token: str,
    user_agent: str | None,
    ip_address: str | None,
) -> AuthResult:
    try:
        token_hash = hash_refresh_token(refresh_token)
    except TokenError as exc:
        raise AuthServiceError(str(exc), 500) from exc

    async with db.begin():
        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        refresh_row = result.scalar_one_or_none()
        if refresh_row is None:
            raise AuthServiceError("Invalid refresh token", 401)

        if refresh_row.revoked_at is not None:
            raise AuthServiceError("Refresh token revoked", 401)

        now = datetime.now(UTC)
        if refresh_row.expires_at <= now:
            refresh_row.revoked_at = now
            raise AuthServiceError("Refresh token expired", 401)

        user_result = await db.execute(select(User).where(User.id == refresh_row.user_id))
        user = user_result.scalar_one_or_none()
        if user is None:
            raise AuthServiceError("User not found", 401)

        tokens = await _issue_local_tokens(
            db=db,
            user=user,
            user_agent=user_agent,
            ip_address=ip_address,
            revoke_existing_id=refresh_row.id,
        )

    return AuthResult(
        user=AuthUserPayload(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            role=user.role.value,
        ),
        tokens=tokens,
    )
