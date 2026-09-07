import os
import sqlite3
from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status

from backend.player_auth_service import get_session_user
from backend.ratings.database import ensure_player_auth_schema, get_connection


PLAYER_SESSION_COOKIE_NAME = "supersonic_player_session"
PLAYER_SESSION_MAX_AGE = 7 * 24 * 60 * 60


def player_cookie_secure() -> bool:
    return os.getenv("APP_ENV", "development").lower() == "production"


def get_player_auth_connection() -> Generator[sqlite3.Connection, None, None]:
    connection = get_connection()
    try:
        ensure_player_auth_schema(connection)
        connection.commit()
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_current_player_user_optional(
    request: Request,
    connection: sqlite3.Connection = Depends(get_player_auth_connection),
) -> str | None:
    return get_session_user(
        connection,
        request.cookies.get(PLAYER_SESSION_COOKIE_NAME),
    )


def require_current_player_user(
    user_id: str | None = Depends(get_current_player_user_optional),
) -> str:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Player authentication required.",
        )
    return user_id
