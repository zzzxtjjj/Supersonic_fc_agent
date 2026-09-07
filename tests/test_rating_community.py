import sqlite3
from pathlib import Path

import pytest

from backend.api import season_data
from backend.ratings.database import get_connection, init_database
from backend.ratings.repository import (
    count_comment_likes,
    create_comment,
    get_comment,
    get_comments_for_player_match,
    get_user_player_id,
    toggle_comment_like,
)


CREATED_AT = "2026-09-06T00:00:00+00:00"


@pytest.fixture
def community_connection(tmp_path: Path):
    database_path = tmp_path / "app.db"
    init_database(database_path)
    connection = get_connection(database_path)
    connection.execute(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        ("user_author", "zhang-xietongjia", CREATED_AT),
    )
    connection.execute(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        ("user_liker", "gan-chenhao", CREATED_AT),
    )
    connection.commit()
    try:
        yield connection
    finally:
        connection.close()


def _create_comment(
    connection: sqlite3.Connection,
    *,
    comment_id: str = "comment_1",
    user_id: str = "user_author",
    content: str = "下半场踢得明显更好",
) -> str:
    return create_comment(
        connection,
        comment_id=comment_id,
        user_id=user_id,
        season_id="25-26",
        match_id="25-26-regular-01",
        player_id="zhang-xietongjia",
        content=content,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
    )


def test_valid_comment_is_created(community_connection: sqlite3.Connection) -> None:
    assert _create_comment(community_connection) == "comment_1"
    row = get_comment(community_connection, "comment_1")
    assert row is not None
    assert row[5] == "下半场踢得明显更好"


def test_empty_comment_is_rejected(community_connection: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _create_comment(community_connection, content="")


def test_whitespace_only_comment_is_rejected(
    community_connection: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _create_comment(community_connection, content="   ")


def test_comment_over_100_characters_is_rejected(
    community_connection: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _create_comment(community_connection, content="评" * 101)


def test_user_can_create_multiple_comments_for_same_player_match(
    community_connection: sqlite3.Connection,
) -> None:
    _create_comment(community_connection, comment_id="comment_1")
    _create_comment(
        community_connection,
        comment_id="comment_2",
        content="最后十分钟控制不错",
    )

    rows = get_comments_for_player_match(
        community_connection,
        "25-26-regular-01",
        "zhang-xietongjia",
    )
    assert [row[0] for row in rows] == ["comment_1", "comment_2"]


def test_first_comment_like_is_created(
    community_connection: sqlite3.Connection,
) -> None:
    _create_comment(community_connection)
    liked = toggle_comment_like(
        community_connection,
        user_id="user_liker",
        comment_id="comment_1",
        created_at=CREATED_AT,
    )

    assert liked is True
    assert count_comment_likes(community_connection, "comment_1") == 1


def test_duplicate_comment_like_is_rejected(
    community_connection: sqlite3.Connection,
) -> None:
    _create_comment(community_connection)
    values = ("user_liker", "comment_1", CREATED_AT)
    community_connection.execute(
        "INSERT INTO comment_likes (user_id, comment_id, created_at) VALUES (?, ?, ?)",
        values,
    )
    with pytest.raises(sqlite3.IntegrityError):
        community_connection.execute(
            """
            INSERT INTO comment_likes (user_id, comment_id, created_at)
            VALUES (?, ?, ?)
            """,
            values,
        )


def test_comment_from_unknown_user_is_rejected(
    community_connection: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _create_comment(community_connection, user_id="missing_user")


def test_like_for_unknown_comment_is_rejected(
    community_connection: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        community_connection.execute(
            """
            INSERT INTO comment_likes (user_id, comment_id, created_at)
            VALUES (?, ?, ?)
            """,
            ("user_liker", "missing_comment", CREATED_AT),
        )


def test_community_schema_initialization_preserves_existing_data(
    community_connection: sqlite3.Connection,
    tmp_path: Path,
) -> None:
    _create_comment(community_connection)
    toggle_comment_like(
        community_connection,
        user_id="user_liker",
        comment_id="comment_1",
        created_at=CREATED_AT,
    )
    community_connection.commit()
    database_path = tmp_path / "app.db"

    init_database(database_path)

    assert community_connection.execute("SELECT COUNT(*) FROM comments").fetchone()[0] == 1
    assert (
        community_connection.execute("SELECT COUNT(*) FROM comment_likes").fetchone()[0]
        == 1
    )


def test_get_user_player_id_uses_identity_key(
    community_connection: sqlite3.Connection,
) -> None:
    assert get_user_player_id(community_connection, "user_author") == "zhang-xietongjia"
    assert get_user_player_id(community_connection, "missing_user") is None


def test_list_seasons_discovers_valid_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for directory in ("25-26", "26-27", "27-28", "notes", "2027-28"):
        (tmp_path / directory).mkdir()
    monkeypatch.setattr(season_data, "SEASON_DATA_ROOT", tmp_path)

    assert season_data.list_seasons() == ["25-26", "26-27", "27-28"]
