import sqlite3
from typing import Any


def get_user_by_player_id(
    connection: sqlite3.Connection,
    player_id: str,
) -> sqlite3.Row | tuple[Any, ...] | None:
    return connection.execute(
        "SELECT id, player_id, created_at FROM users WHERE player_id = ?",
        (player_id,),
    ).fetchone()


def get_user_by_id(
    connection: sqlite3.Connection,
    user_id: str,
) -> sqlite3.Row | tuple[Any, ...] | None:
    return connection.execute(
        "SELECT id, player_id, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()


def get_credentials(
    connection: sqlite3.Connection,
    user_id: str,
) -> sqlite3.Row | tuple[Any, ...] | None:
    return connection.execute(
        """
        SELECT user_id, password_hash, activated_at, created_at
        FROM user_credentials
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()


def create_credentials(
    connection: sqlite3.Connection,
    *,
    user_id: str,
    password_hash: str,
    activated_at: str,
    created_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO user_credentials (
            user_id, password_hash, activated_at, created_at
        ) VALUES (?, ?, ?, ?)
        """,
        (user_id, password_hash, activated_at, created_at),
    )


def invalidate_open_invites(
    connection: sqlite3.Connection,
    *,
    user_id: str,
    used_at: str,
) -> None:
    connection.execute(
        """
        UPDATE player_invites
        SET used_at = ?
        WHERE user_id = ? AND used_at IS NULL
        """,
        (used_at, user_id),
    )


def create_invite(
    connection: sqlite3.Connection,
    *,
    invite_id: str,
    user_id: str,
    code_hash: str,
    expires_at: str,
    created_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO player_invites (
            id, user_id, code_hash, expires_at, used_at, created_at
        ) VALUES (?, ?, ?, ?, NULL, ?)
        """,
        (invite_id, user_id, code_hash, expires_at, created_at),
    )


def get_invite_by_hash(
    connection: sqlite3.Connection,
    code_hash: str,
) -> sqlite3.Row | tuple[Any, ...] | None:
    return connection.execute(
        """
        SELECT id, user_id, code_hash, expires_at, used_at, created_at
        FROM player_invites
        WHERE code_hash = ?
        """,
        (code_hash,),
    ).fetchone()


def mark_invite_used(
    connection: sqlite3.Connection,
    *,
    invite_id: str,
    used_at: str,
) -> bool:
    cursor = connection.execute(
        """
        UPDATE player_invites
        SET used_at = ?
        WHERE id = ? AND used_at IS NULL
        """,
        (used_at, invite_id),
    )
    return cursor.rowcount == 1


def create_session(
    connection: sqlite3.Connection,
    *,
    token_hash: str,
    user_id: str,
    expires_at: str,
    created_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO player_sessions (token_hash, user_id, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (token_hash, user_id, expires_at, created_at),
    )


def get_session(
    connection: sqlite3.Connection,
    token_hash: str,
) -> sqlite3.Row | tuple[Any, ...] | None:
    return connection.execute(
        """
        SELECT token_hash, user_id, expires_at, created_at
        FROM player_sessions
        WHERE token_hash = ?
        """,
        (token_hash,),
    ).fetchone()


def delete_session(connection: sqlite3.Connection, token_hash: str) -> None:
    connection.execute(
        "DELETE FROM player_sessions WHERE token_hash = ?",
        (token_hash,),
    )
