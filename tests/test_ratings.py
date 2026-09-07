import json
import sqlite3
from pathlib import Path

import pytest

from backend.ratings.database import (
    RATING_LIKES_TABLE_SQL,
    RATINGS_TABLE_SQL,
    get_connection,
    init_database,
    synchronize_empty_rating_schema,
)
from backend.ratings.seed import PLACEHOLDER_PLAYER_ID, seed_rating_members
from backend.ratings.service import submit_rating


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAYERS_PATH = PROJECT_ROOT / "data" / "seasons" / "25-26" / "players.json"
MATCHES_PATH = PROJECT_ROOT / "data" / "seasons" / "25-26" / "matches.json"
CREATED_AT = "2026-09-06T00:00:00+00:00"


@pytest.fixture
def rating_connection(tmp_path: Path):
    database_path = tmp_path / "app.db"
    init_database(database_path)
    connection = get_connection(database_path)
    connection.execute(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        ("user_author", "li-yunfan", CREATED_AT),
    )
    connection.execute(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        ("user_liker", "he-bolin", CREATED_AT),
    )
    connection.commit()
    try:
        yield connection
    finally:
        connection.close()


def _insert_rating(
    connection: sqlite3.Connection,
    *,
    rating_id: str = "rating_1",
    user_id: str = "user_author",
    match_id: str = "25-26-regular-01",
    player_id: str = "zhang-xietongjia",
    score: float = 9.5,
    reason: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO ratings (
            id, user_id, season_id, match_id, player_id,
            score, reason, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rating_id,
            user_id,
            "25-26",
            match_id,
            player_id,
            score,
            reason,
            CREATED_AT,
            CREATED_AT,
        ),
    )


def _replace_with_legacy_rating_tables(connection: sqlite3.Connection) -> None:
    connection.execute("DROP TABLE rating_likes")
    connection.execute("DROP TABLE ratings")
    connection.execute(
        """
        CREATE TABLE ratings (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            season_id TEXT NOT NULL,
            match_id TEXT NOT NULL,
            player_id TEXT NOT NULL,
            score REAL NOT NULL CHECK (score >= 0 AND score <= 10),
            reason TEXT CHECK (reason IS NULL OR length(reason) <= 100),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (user_id, match_id, player_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE rating_likes (
            user_id TEXT NOT NULL,
            rating_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (user_id, rating_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (rating_id) REFERENCES ratings(id)
        )
        """
    )
    connection.commit()


def test_valid_9_5_score_is_accepted(rating_connection: sqlite3.Connection) -> None:
    _insert_rating(rating_connection, score=9.5)
    assert rating_connection.execute("SELECT score FROM ratings").fetchone()[0] == 9.5


def test_valid_8_1_score_is_accepted(rating_connection: sqlite3.Connection) -> None:
    _insert_rating(rating_connection, score=8.1)
    assert rating_connection.execute("SELECT score FROM ratings").fetchone()[0] == 8.1


def test_score_above_10_is_rejected(rating_connection: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _insert_rating(rating_connection, score=11)


def test_negative_score_is_rejected(rating_connection: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _insert_rating(rating_connection, score=-0.5)


def test_non_tenth_step_score_is_rejected(rating_connection: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _insert_rating(rating_connection, score=8.27)


def test_reason_over_100_characters_is_rejected(
    rating_connection: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _insert_rating(rating_connection, reason="评" * 101)


def test_duplicate_user_match_player_rating_is_rejected(
    rating_connection: sqlite3.Connection,
) -> None:
    _insert_rating(rating_connection)
    with pytest.raises(sqlite3.IntegrityError):
        _insert_rating(rating_connection, rating_id="rating_2")


def test_unknown_rating_user_is_rejected(
    rating_connection: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _insert_rating(rating_connection, user_id="missing_user")


def test_duplicate_like_is_rejected(rating_connection: sqlite3.Connection) -> None:
    _insert_rating(rating_connection)
    values = ("user_liker", "rating_1", CREATED_AT)
    rating_connection.execute(
        "INSERT INTO rating_likes (user_id, rating_id, created_at) VALUES (?, ?, ?)",
        values,
    )
    with pytest.raises(sqlite3.IntegrityError):
        rating_connection.execute(
            "INSERT INTO rating_likes (user_id, rating_id, created_at) VALUES (?, ?, ?)",
            values,
        )


def test_like_for_unknown_rating_is_rejected(
    rating_connection: sqlite3.Connection,
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        rating_connection.execute(
            "INSERT INTO rating_likes (user_id, rating_id, created_at) VALUES (?, ?, ?)",
            ("user_liker", "missing_rating", CREATED_AT),
        )


def test_submit_rating_allows_self_rating_and_normalizes_reason(
    rating_connection: sqlite3.Connection,
) -> None:
    rating_connection.execute(
        "INSERT INTO season_rating_members (season_id, user_id) VALUES (?, ?)",
        ("25-26", "user_author"),
    )

    actual_id = submit_rating(
        rating_connection,
        rating_id="rating_self",
        user_id="user_author",
        season_id="25-26",
        match_id="25-26-regular-01",
        player_id="li-yunfan",
        score=9,
        reason="  本场表现稳定  ",
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
    )
    row = rating_connection.execute(
        "SELECT id, score, reason FROM ratings WHERE id = ?",
        (actual_id,),
    ).fetchone()

    assert row == ("rating_self", 9.0, "本场表现稳定")


def test_submit_rating_updates_reason_and_normalizes_blank_to_none(
    rating_connection: sqlite3.Connection,
) -> None:
    rating_connection.execute(
        "INSERT INTO season_rating_members (season_id, user_id) VALUES (?, ?)",
        ("25-26", "user_author"),
    )
    common = {
        "connection": rating_connection,
        "user_id": "user_author",
        "season_id": "25-26",
        "match_id": "25-26-regular-01",
        "player_id": "li-yunfan",
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
    }
    submit_rating(
        **common,
        rating_id="rating_original",
        score=8.5,
        reason="第一次理由",
    )
    actual_id = submit_rating(
        **common,
        rating_id="rating_replacement",
        score=9.5,
        reason="   ",
    )
    row = rating_connection.execute(
        "SELECT id, score, reason FROM ratings WHERE id = ?",
        (actual_id,),
    ).fetchone()

    assert actual_id == "rating_original"
    assert row == ("rating_original", 9.5, None)


def test_seed_uses_real_ids_and_is_idempotent(tmp_path: Path) -> None:
    database_path = tmp_path / "app.db"
    first = seed_rating_members(database_path, PLAYERS_PATH)
    second = seed_rating_members(database_path, PLAYERS_PATH)

    players = json.loads(PLAYERS_PATH.read_text(encoding="utf-8"))["players"]
    expected_player_ids = {player["id"] for player in players}
    connection = get_connection(database_path)
    try:
        users = connection.execute("SELECT id, player_id FROM users").fetchall()
        members = connection.execute(
            "SELECT season_id, user_id FROM season_rating_members"
        ).fetchall()
        rating_count = connection.execute("SELECT COUNT(*) FROM ratings").fetchone()[0]
        like_count = connection.execute("SELECT COUNT(*) FROM rating_likes").fetchone()[0]
    finally:
        connection.close()

    assert len(expected_player_ids) == 20
    assert {row[1] for row in users} == expected_player_ids
    assert {row[0] for row in users} == {f"user_{value}" for value in expected_player_ids}
    assert len(members) == 20
    assert {row[0] for row in members} == {"25-26"}
    assert rating_count == 0
    assert like_count == 0
    assert first["created_users"] == 20
    assert first["created_memberships"] == 20
    assert second["created_users"] == 0
    assert second["created_memberships"] == 0


def test_seed_removes_only_the_known_placeholder(tmp_path: Path) -> None:
    database_path = tmp_path / "app.db"
    init_database(database_path)
    connection = get_connection(database_path)
    connection.execute(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        ("user_zhang_xietongjia", PLACEHOLDER_PLAYER_ID, CREATED_AT),
    )
    connection.execute(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        ("existing_real_user", "existing-real-player", CREATED_AT),
    )
    connection.commit()
    connection.close()

    seed_rating_members(database_path, PLAYERS_PATH)

    connection = get_connection(database_path)
    try:
        placeholder = connection.execute(
            "SELECT 1 FROM users WHERE player_id = ?",
            (PLACEHOLDER_PLAYER_ID,),
        ).fetchone()
        real_user = connection.execute(
            "SELECT 1 FROM users WHERE id = ?",
            ("existing_real_user",),
        ).fetchone()
    finally:
        connection.close()

    assert placeholder is None
    assert real_user is not None


def test_empty_legacy_schema_is_synchronized_without_seed_data(tmp_path: Path) -> None:
    database_path = tmp_path / "app.db"
    init_database(database_path)
    connection = get_connection(database_path)
    _replace_with_legacy_rating_tables(connection)
    connection.close()

    assert synchronize_empty_rating_schema(database_path) is True

    connection = get_connection(database_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            _insert_rating(connection, score=8.27)
    finally:
        connection.close()


def test_populated_legacy_schema_is_not_rebuilt(tmp_path: Path) -> None:
    database_path = tmp_path / "app.db"
    init_database(database_path)
    connection = get_connection(database_path)
    connection.execute(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        ("user_author", "li-yunfan", CREATED_AT),
    )
    _replace_with_legacy_rating_tables(connection)
    _insert_rating(connection, score=8.27)
    connection.commit()
    connection.close()

    with pytest.raises(RuntimeError, match="automatic synchronization refused"):
        synchronize_empty_rating_schema(database_path)

    connection = get_connection(database_path)
    try:
        assert connection.execute("SELECT COUNT(*) FROM ratings").fetchone()[0] == 1
    finally:
        connection.close()


def test_half_step_schema_is_migrated_without_losing_ratings_or_likes(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "app.db"
    init_database(database_path)
    connection = get_connection(database_path)
    connection.execute(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        ("user_author", "li-yunfan", CREATED_AT),
    )
    connection.execute(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        ("user_liker", "he-bolin", CREATED_AT),
    )
    old_schema = RATINGS_TABLE_SQL.replace(
        "ABS(score * 10 - ROUND(score * 10)) < 0.000001",
        "score * 2 = CAST(score * 2 AS INTEGER)",
    )
    connection.execute("DROP TABLE rating_likes")
    connection.execute("DROP TABLE ratings")
    connection.execute(old_schema)
    connection.execute(RATING_LIKES_TABLE_SQL)
    _insert_rating(connection, score=9.5)
    connection.execute(
        "INSERT INTO rating_likes (user_id, rating_id, created_at) VALUES (?, ?, ?)",
        ("user_liker", "rating_1", CREATED_AT),
    )
    connection.commit()
    connection.close()

    init_database(database_path)

    connection = get_connection(database_path)
    try:
        assert connection.execute("SELECT score FROM ratings").fetchall() == [(9.5,)]
        assert connection.execute("SELECT COUNT(*) FROM rating_likes").fetchone()[0] == 1
        _insert_rating(
            connection,
            rating_id="rating_tenth",
            match_id="25-26-regular-02",
            score=8.1,
        )
    finally:
        connection.close()


def test_json_ids_are_not_duplicated_or_moved_into_sqlite() -> None:
    players = json.loads(PLAYERS_PATH.read_text(encoding="utf-8"))["players"]
    matches = json.loads(MATCHES_PATH.read_text(encoding="utf-8"))["matches"]

    assert len(players) == 20
    assert len({player["id"] for player in players}) == 20
    assert len(matches) == 9
    assert len({match["id"] for match in matches}) == 9
