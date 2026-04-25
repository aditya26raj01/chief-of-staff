import uuid
from typing import Annotated, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.token_utils import TokenError, decode_access_token
from app.auth.user_entity import User
from app.core.database.postgres import get_db_session

bearer_scheme = HTTPBearer(auto_error=True)

CredentialsDep = Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    credentials: CredentialsDep,
    db: DBSessionDep,
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not isinstance(sub, str):
            raise TokenError("Missing subject in token")
        user_id = uuid.UUID(sub)
    except (TokenError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        ) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = cast(User | None, result.scalar_one_or_none())
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
