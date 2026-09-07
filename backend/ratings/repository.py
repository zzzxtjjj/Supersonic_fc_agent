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


def get_user_player_id(
    connection: sqlite3.Connection,
    user_id: str,
) -> str | None:
    row = connection.execute(
        "SELECT player_id FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    return None if row is None else str(row[0])


def is_rating_member(
    connection: sqlite3.Connection,
    user_id: str,
    season_id: str,
) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM season_rating_members
        WHERE user_id = ? AND season_id = ?
        """,
        (user_id, season_id),
    ).fetchone()
    return row is not None


def create_or_update_rating(
    connection: sqlite3.Connection,
    # 参数必须写参数名，不能只靠位置传
    *,
    rating_id: str,
    user_id: str,
    season_id: str,
    match_id: str,
    player_id: str,
    score: float,
    reason: str | None,
    created_at: str,
    updated_at: str,
) -> str:
    connection.execute(
        """
        INSERT INTO ratings (
            id, user_id, season_id, match_id, player_id,
            score, reason, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (user_id, match_id, player_id) DO UPDATE SET
            score = excluded.score,
            reason = excluded.reason,
            updated_at = excluded.updated_at
        """,
        (
            rating_id,
            user_id,
            season_id,
            match_id,
            player_id,
            score,
            reason,
            created_at,
            updated_at,
        ),
    )
    row = connection.execute(
        """
        SELECT id FROM ratings
        WHERE user_id = ? AND match_id = ? AND player_id = ?
        """,
        (user_id, match_id, player_id),
    ).fetchone()
    return str(row[0])


def delete_rating(connection: sqlite3.Connection, rating_id: str) -> bool:
    connection.execute(
        "DELETE FROM rating_likes WHERE rating_id = ?",
        (rating_id,),
    )
    cursor = connection.execute(
        "DELETE FROM ratings WHERE id = ?",
        (rating_id,),
    )
    return cursor.rowcount > 0


def get_rating(
    connection: sqlite3.Connection,
    rating_id: str,
) -> sqlite3.Row | tuple[Any, ...] | None:
    return connection.execute(
        "SELECT * FROM ratings WHERE id = ?",
        (rating_id,),
    ).fetchone()


def get_match_ratings(
    connection: sqlite3.Connection,
    match_id: str,
) -> list[sqlite3.Row | tuple[Any, ...]]:
    return connection.execute(
        "SELECT * FROM ratings WHERE match_id = ? ORDER BY created_at, id",
        (match_id,),
    ).fetchall()


def get_user_rating_for_player_match(
    connection: sqlite3.Connection,
    user_id: str,
    match_id: str,
    player_id: str,
) -> sqlite3.Row | tuple[Any, ...] | None:
    return connection.execute(
        """
        SELECT * FROM ratings
        WHERE user_id = ? AND match_id = ? AND player_id = ?
        """,
        (user_id, match_id, player_id),
    ).fetchone()


def is_rating_liked_by_user(
    connection: sqlite3.Connection,
    user_id: str,
    rating_id: str,
) -> bool:
    return connection.execute(
        "SELECT 1 FROM rating_likes WHERE user_id = ? AND rating_id = ?",
        (user_id, rating_id),
    ).fetchone() is not None


def toggle_like(
    connection: sqlite3.Connection,
    *,
    user_id: str,
    rating_id: str,
    created_at: str,
) -> bool:
    existing = connection.execute(
        """
        SELECT 1 FROM rating_likes
        WHERE user_id = ? AND rating_id = ?
        """,
        (user_id, rating_id),
    ).fetchone()
    if existing is not None:
        connection.execute(
            "DELETE FROM rating_likes WHERE user_id = ? AND rating_id = ?",
            (user_id, rating_id),
        )
        return False

    connection.execute(
        """
        INSERT INTO rating_likes (user_id, rating_id, created_at)
        VALUES (?, ?, ?)
        """,
        (user_id, rating_id, created_at),
    )
    return True


def count_rating_likes(
    connection: sqlite3.Connection,
    rating_id: str,
) -> int:
    row = connection.execute(
        "SELECT COUNT(*) FROM rating_likes WHERE rating_id = ?",
        (rating_id,),
    ).fetchone()
    return int(row[0])


def create_comment(
    connection: sqlite3.Connection,
    *,
    comment_id: str,
    user_id: str,
    season_id: str,
    match_id: str,
    player_id: str,
    content: str,
    created_at: str,
    updated_at: str,
) -> str:
    connection.execute(
        """
        INSERT INTO comments (
            id, user_id, season_id, match_id, player_id,
            content, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            comment_id,
            user_id,
            season_id,
            match_id,
            player_id,
            content,
            created_at,
            updated_at,
        ),
    )
    return comment_id


def get_comment(
    connection: sqlite3.Connection,
    comment_id: str,
) -> sqlite3.Row | tuple[Any, ...] | None:
    return connection.execute(
        "SELECT * FROM comments WHERE id = ?",
        (comment_id,),
    ).fetchone()


def get_comments_for_player_match(
    connection: sqlite3.Connection,
    match_id: str,
    player_id: str,
) -> list[sqlite3.Row | tuple[Any, ...]]:
    return connection.execute(
        """
        SELECT *
        FROM comments
        WHERE match_id = ? AND player_id = ?
        ORDER BY created_at, id
        """,
        (match_id, player_id),
    ).fetchall()


def delete_comment(connection: sqlite3.Connection, comment_id: str) -> bool:
    connection.execute(
        "DELETE FROM comment_likes WHERE comment_id = ?",
        (comment_id,),
    )
    cursor = connection.execute(
        "DELETE FROM comments WHERE id = ?",
        (comment_id,),
    )
    return cursor.rowcount > 0


def toggle_comment_like(
    connection: sqlite3.Connection,
    *,
    user_id: str,
    comment_id: str,
    created_at: str,
) -> bool:
    existing = connection.execute(
        """
        SELECT 1 FROM comment_likes
        WHERE user_id = ? AND comment_id = ?
        """,
        (user_id, comment_id),
    ).fetchone()
    if existing is not None:
        connection.execute(
            "DELETE FROM comment_likes WHERE user_id = ? AND comment_id = ?",
            (user_id, comment_id),
        )
        return False

    connection.execute(
        """
        INSERT INTO comment_likes (user_id, comment_id, created_at)
        VALUES (?, ?, ?)
        """,
        (user_id, comment_id, created_at),
    )
    return True


def count_comment_likes(
    connection: sqlite3.Connection,
    comment_id: str,
) -> int:
    row = connection.execute(
        "SELECT COUNT(*) FROM comment_likes WHERE comment_id = ?",
        (comment_id,),
    ).fetchone()
    return int(row[0])


def is_comment_liked_by_user(
    connection: sqlite3.Connection,
    user_id: str,
    comment_id: str,
) -> bool:
    return connection.execute(
        "SELECT 1 FROM comment_likes WHERE user_id = ? AND comment_id = ?",
        (user_id, comment_id),
    ).fetchone() is not None
