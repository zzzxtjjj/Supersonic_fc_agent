import hashlib
import secrets
import sqlite3
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.api.season_data import find_player
from backend.auth import hash_password, verify_password
from backend.player_auth_repository import (
    create_credentials,
    create_invite,
    create_session,
    delete_session,
    get_credentials,
    get_invite_by_hash,
    get_session,
    get_user_by_id,
    get_user_by_player_id,
    invalidate_open_invites,
    mark_invite_used,
)


INVITE_TTL = timedelta(days=7)
PLAYER_SESSION_TTL = timedelta(days=7)


class PlayerAuthError(ValueError):
    pass


class PlayerAuthNotFound(PlayerAuthError):
    pass


class PlayerAuthConflict(PlayerAuthError):
    pass


class PlayerAuthenticationFailed(PlayerAuthError):
    pass


class PlayerAccountNotActivated(PlayerAuthError):
    pass


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_player_invite(
    connection: sqlite3.Connection,
    *,
    player_id: str,
) -> dict[str, str]:
    if find_player(player_id) is None:
        raise PlayerAuthNotFound(f"Official player not found: {player_id}")
    user = get_user_by_player_id(connection, player_id)
    if user is None:
        raise PlayerAuthNotFound(f"Rating user not found for player: {player_id}")

    now = _now()
    invite_code = secrets.token_urlsafe(24)
    expires_at = now + INVITE_TTL
    invalidate_open_invites(connection, user_id=str(user[0]), used_at=_iso(now))
    create_invite(
        connection,
        invite_id=f"invite_{uuid.uuid4().hex}",
        user_id=str(user[0]),
        code_hash=_token_hash(invite_code),
        expires_at=_iso(expires_at),
        created_at=_iso(now),
    )
    return {
        "player_id": player_id,
        "invite_code": invite_code,
        "expires_at": _iso(expires_at),
    }


def activate_player(
    connection: sqlite3.Connection,
    *,
    invite_code: str,
    password: str,
) -> str:
    invite = get_invite_by_hash(connection, _token_hash(invite_code.strip()))
    if invite is None:
        raise PlayerAuthError("Invalid invite code.")
    if invite[4] is not None:
        raise PlayerAuthConflict("Invite code has already been used or revoked.")
    now = _now()
    if _parse(str(invite[3])) <= now:
        raise PlayerAuthError("Invite code has expired.")
    user_id = str(invite[1])
    if get_credentials(connection, user_id) is not None:
        raise PlayerAuthConflict("Player account is already activated.")
    if not mark_invite_used(connection, invite_id=str(invite[0]), used_at=_iso(now)):
        raise PlayerAuthConflict("Invite code has already been used or revoked.")
    create_credentials(
        connection,
        user_id=user_id,
        password_hash=hash_password(password),
        activated_at=_iso(now),
        created_at=_iso(now),
    )
    return user_id


def login_player(
    connection: sqlite3.Connection,
    *,
    player_id: str,
    password: str,
) -> tuple[str, str, datetime]:
    user = get_user_by_player_id(connection, player_id)
    if user is None:
        raise PlayerAuthenticationFailed("Invalid player id or password.")
    user_id = str(user[0])
    credentials = get_credentials(connection, user_id)
    if credentials is None:
        raise PlayerAccountNotActivated("Player account has not been activated.")
    if not verify_password(password, str(credentials[1])):
        raise PlayerAuthenticationFailed("Invalid player id or password.")

    token = secrets.token_urlsafe(32)
    now = _now()
    expires_at = now + PLAYER_SESSION_TTL
    create_session(
        connection,
        token_hash=_token_hash(token),
        user_id=user_id,
        expires_at=_iso(expires_at),
        created_at=_iso(now),
    )
    return token, user_id, expires_at


def get_session_user(
    connection: sqlite3.Connection,
    session_token: str | None,
) -> str | None:
    if not session_token:
        return None
    token_hash = _token_hash(session_token)
    session = get_session(connection, token_hash)
    if session is None:
        return None
    if _parse(str(session[2])) <= _now():
        delete_session(connection, token_hash)
        return None
    return str(session[1])


def logout_player(
    connection: sqlite3.Connection,
    session_token: str | None,
) -> None:
    if session_token:
        delete_session(connection, _token_hash(session_token))


def get_player_auth_identity(
    connection: sqlite3.Connection,
    user_id: str,
) -> dict[str, Any]:
    user = get_user_by_id(connection, user_id)
    if user is None:
        raise PlayerAuthNotFound("Player user not found.")
    player_id = str(user[1])
    official = find_player(player_id)
    if official is None:
        raise PlayerAuthNotFound("Official player profile not found.")
    player = official["player"]
    return {
        "id": user_id,
        "player_id": player_id,
        "name": player["name"],
        "photo_url": player.get("photo_url"),
    }
