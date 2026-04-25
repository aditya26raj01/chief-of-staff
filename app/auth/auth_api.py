from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_deps import get_current_user
from app.auth.auth_service import (
    AuthResult,
    AuthServiceError,
    build_google_init_url,
    handle_google_callback,
    refresh_session,
)
from app.auth.user_entity import User
from app.core.database.postgres import get_db_session

router = APIRouter(prefix="/auth", tags=["auth"])


class UserResponse(BaseModel):
    id: str
    email: str
    displayName: str
    avatarUrl: str
    role: str


class TokensResponse(BaseModel):
    accessToken: str
    refreshToken: str


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokensResponse


class RefreshRequest(BaseModel):
    refreshToken: str


DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _map_auth_response(result: AuthResult) -> AuthResponse:
    return AuthResponse(
        user=UserResponse(
            id=result.user.id,
            email=result.user.email,
            displayName=result.user.display_name,
            avatarUrl=result.user.avatar_url,
            role=result.user.role,
        ),
        tokens=TokensResponse(
            accessToken=result.tokens.access_token,
            refreshToken=result.tokens.refresh_token,
        ),
    )


@router.get("/google/init")
async def google_init() -> RedirectResponse:
    return RedirectResponse(url=build_google_init_url())


@router.get("/google/callback", response_model=AuthResponse)
async def google_callback(
    request: Request,
    db: DBSessionDep,
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> AuthResponse:
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code")

    try:
        result = await handle_google_callback(
            db=db,
            code=code,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return _map_auth_response(result)


@router.post("/refresh", response_model=AuthResponse)
async def refresh_tokens(
    payload: RefreshRequest,
    request: Request,
    db: DBSessionDep,
) -> AuthResponse:
    try:
        result = await refresh_session(
            db=db,
            refresh_token=payload.refreshToken,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except AuthServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return _map_auth_response(result)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUserDep) -> UserResponse:
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        displayName=current_user.display_name,
        avatarUrl=current_user.avatar_url,
        role=current_user.role.value,
    )
