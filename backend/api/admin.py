from fastapi import APIRouter, HTTPException, Request, Response, status

from backend.auth import (
    SESSION_COOKIE_NAME,
    authenticate_admin,
    create_admin_session,
    destroy_admin_session,
    get_admin_config,
    is_admin_session,
)
from backend.schemas.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminSessionResponse,
)


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=AdminLoginResponse)
async def login(payload: AdminLoginRequest, response: Response) -> AdminLoginResponse:
    if not authenticate_admin(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator credentials.",
        )

    config = get_admin_config()
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured.",
        )
    session_cookie = create_admin_session()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_cookie,
        httponly=True,
        secure=config.secure_cookie,
        samesite="strict",
        path="/",
    )
    return AdminLoginResponse(authenticated=True, username=config.username)


@router.post("/logout", response_model=AdminSessionResponse)
async def logout(request: Request, response: Response) -> AdminSessionResponse:
    destroy_admin_session(request.cookies.get(SESSION_COOKIE_NAME))
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=(get_admin_config().secure_cookie if get_admin_config() else False),
        samesite="strict",
    )
    return AdminSessionResponse(authenticated=False)


@router.get("/me", response_model=AdminSessionResponse)
async def me(request: Request) -> AdminSessionResponse:
    return AdminSessionResponse(
        authenticated=is_admin_session(request.cookies.get(SESSION_COOKIE_NAME))
    )
