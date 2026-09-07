import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from backend.auth import require_admin
from backend.player_auth import (
    PLAYER_SESSION_COOKIE_NAME,
    PLAYER_SESSION_MAX_AGE,
    get_current_player_user_optional,
    get_player_auth_connection,
    player_cookie_secure,
    require_current_player_user,
)
from backend.player_auth_service import (
    PlayerAccountNotActivated,
    PlayerAuthConflict,
    PlayerAuthError,
    PlayerAuthenticationFailed,
    PlayerAuthNotFound,
    activate_player,
    get_player_auth_identity,
    issue_player_invite,
    login_player,
    logout_player,
)
from backend.ratings.service import is_supersonic_player
from backend.schemas.player_auth import (
    PlayerActivateRequest,
    PlayerActivateResponse,
    PlayerInviteResponse,
    PlayerLoginRequest,
    PlayerLoginResponse,
    PlayerLogoutResponse,
    PlayerMeResponse,
)


router = APIRouter(tags=["player-auth"])


def _http_error(exc: PlayerAuthError) -> HTTPException:
    if isinstance(exc, PlayerAuthNotFound):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, PlayerAuthConflict):
        code = status.HTTP_409_CONFLICT
    elif isinstance(exc, PlayerAccountNotActivated):
        code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, PlayerAuthenticationFailed):
        code = status.HTTP_401_UNAUTHORIZED
    else:
        code = status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=code, detail=str(exc))


@router.post(
    "/admin/player-invites/{player_id}",
    response_model=PlayerInviteResponse,
    dependencies=[Depends(require_admin)],
)
async def create_player_invite(
    player_id: str,
    connection: sqlite3.Connection = Depends(get_player_auth_connection),
) -> PlayerInviteResponse:
    try:
        return PlayerInviteResponse(
            **issue_player_invite(connection, player_id=player_id)
        )
    except PlayerAuthError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/player-auth/activate",
    response_model=PlayerActivateResponse,
)
async def activate(
    payload: PlayerActivateRequest,
    connection: sqlite3.Connection = Depends(get_player_auth_connection),
) -> PlayerActivateResponse:
    try:
        activate_player(
            connection,
            invite_code=payload.invite_code,
            password=payload.password,
        )
    except PlayerAuthError as exc:
        raise _http_error(exc) from exc
    return PlayerActivateResponse(activated=True)


@router.post(
    "/player-auth/login",
    response_model=PlayerLoginResponse,
)
async def login(
    payload: PlayerLoginRequest,
    response: Response,
    connection: sqlite3.Connection = Depends(get_player_auth_connection),
) -> PlayerLoginResponse:
    try:
        token, _user_id, expires_at = login_player(
            connection,
            player_id=payload.player_id,
            password=payload.password,
        )
    except PlayerAuthError as exc:
        raise _http_error(exc) from exc
    response.set_cookie(
        key=PLAYER_SESSION_COOKIE_NAME,
        value=token,
        max_age=PLAYER_SESSION_MAX_AGE,
        expires=expires_at,
        httponly=True,
        secure=player_cookie_secure(),
        samesite="strict",
        path="/",
    )
    return PlayerLoginResponse(authenticated=True)


@router.get("/player-auth/me", response_model=PlayerMeResponse)
async def me(
    user_id: str = Depends(require_current_player_user),
    connection: sqlite3.Connection = Depends(get_player_auth_connection),
) -> PlayerMeResponse:
    try:
        identity = get_player_auth_identity(connection, user_id)
    except PlayerAuthError as exc:
        raise _http_error(exc) from exc
    return PlayerMeResponse(
        authenticated=True,
        user=identity,
        is_supersonic_player=is_supersonic_player(connection, user_id),
    )


@router.post("/player-auth/logout", response_model=PlayerLogoutResponse)
async def logout(
    request: Request,
    response: Response,
    _user_id: str | None = Depends(get_current_player_user_optional),
    connection: sqlite3.Connection = Depends(get_player_auth_connection),
) -> PlayerLogoutResponse:
    logout_player(
        connection,
        request.cookies.get(PLAYER_SESSION_COOKIE_NAME),
    )
    response.delete_cookie(
        key=PLAYER_SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=player_cookie_secure(),
        samesite="strict",
    )
    return PlayerLogoutResponse(authenticated=False)
