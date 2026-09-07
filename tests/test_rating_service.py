import sqlite3
from pathlib import Path

import pytest

from backend.ratings.database import get_connection, init_database
from backend.ratings.repository import create_comment, create_or_update_rating
from backend.ratings.service import (
    is_supersonic_player,
    submit_comment,
    submit_rating,
    toggle_comment_like,
    toggle_rating_like,
)


CREATED_AT = "2026-09-06T00:00:00+00:00"


@pytest.fixture
def service_connection(tmp_path: Path):
    database_path = tmp_path / "app.db"
    init_database(database_path)
    connection = get_connection(database_path)
    users = (
        ("user_old_player", "yao-hanrong", CREATED_AT),
        ("user_other_player", "gan-chenhao", CREATED_AT),
        ("user_outsider", "never-rostered-player", CREATED_AT),
    )
    connection.executemany(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        users,
    )
    connection.execute(
        "INSERT INTO season_rating_members (season_id, user_id) VALUES (?, ?)",
        ("25-26", "user_old_player"),
    )
    connection.commit()
    try:
        yield connection
    finally:
        connection.close()


def _create_rating(
    connection: sqlite3.Connection,
    *,
    rating_id: str = "rating_other_season",
    user_id: str = "user_other_player",
    season_id: str = "27-28",
    player_id: str = "gan-chenhao",
) -> str:
    return create_or_update_rating(
        connection,
        rating_id=rating_id,
        user_id=user_id,
        season_id=season_id,
        match_id=f"{season_id}-match-01",
        player_id=player_id,
        score=9.0,
        reason=None,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
    )


def _create_comment(
    connection: sqlite3.Connection,
    *,
    comment_id: str = "comment_existing",
    user_id: str = "user_other_player",
) -> str:
    return create_comment(
        connection,
        comment_id=comment_id,
        user_id=user_id,
        season_id="27-28",
        match_id="27-28-match-01",
        player_id="gan-chenhao",
        content="已有评论",
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
    )


def test_registered_player_from_any_roster_is_supersonic_player(
    service_connection: sqlite3.Connection,
) -> None:
    assert is_supersonic_player(service_connection, "user_old_player") is True


def test_registered_user_whose_player_id_is_never_rostered_is_not_supersonic(
    service_connection: sqlite3.Connection,
) -> None:
    assert is_supersonic_player(service_connection, "user_outsider") is False


def test_missing_user_is_not_supersonic_player(
    service_connection: sqlite3.Connection,
) -> None:
    assert is_supersonic_player(service_connection, "missing_user") is False


def test_old_player_can_like_rating_from_another_season(
    service_connection: sqlite3.Connection,
) -> None:
    _create_rating(service_connection)

    liked = toggle_rating_like(
        service_connection,
        user_id="user_old_player",
        rating_id="rating_other_season",
        created_at=CREATED_AT,
    )

    assert liked is True


def test_player_can_like_own_rating(service_connection: sqlite3.Connection) -> None:
    _create_rating(
        service_connection,
        rating_id="rating_self",
        user_id="user_old_player",
        player_id="yao-hanrong",
    )

    liked = toggle_rating_like(
        service_connection,
        user_id="user_old_player",
        rating_id="rating_self",
        created_at=CREATED_AT,
    )

    assert liked is True


def test_old_player_can_comment_on_another_season(
    service_connection: sqlite3.Connection,
) -> None:
    comment_id = submit_comment(
        service_connection,
        comment_id="comment_other_season",
        user_id="user_old_player",
        season_id="27-28",
        match_id="27-28-match-01",
        player_id="gan-chenhao",
        content="  跨赛季仍可参与社区互动  ",
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
    )
    stored = service_connection.execute(
        "SELECT content FROM comments WHERE id = ?",
        (comment_id,),
    ).fetchone()

    assert stored == ("跨赛季仍可参与社区互动",)


def test_player_can_comment_on_self(service_connection: sqlite3.Connection) -> None:
    comment_id = submit_comment(
        service_connection,
        comment_id="comment_self",
        user_id="user_old_player",
        season_id="27-28",
        match_id="27-28-match-01",
        player_id="yao-hanrong",
        content="评论自己的表现",
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
    )

    assert comment_id == "comment_self"


def test_player_can_like_own_comment(service_connection: sqlite3.Connection) -> None:
    _create_comment(
        service_connection,
        comment_id="comment_self",
        user_id="user_old_player",
    )

    liked = toggle_comment_like(
        service_connection,
        user_id="user_old_player",
        comment_id="comment_self",
        created_at=CREATED_AT,
    )

    assert liked is True


def test_non_supersonic_user_cannot_comment_or_like(
    service_connection: sqlite3.Connection,
) -> None:
    _create_rating(service_connection)
    _create_comment(service_connection)

    with pytest.raises(ValueError, match="社区互动权限"):
        submit_comment(
            service_connection,
            comment_id="comment_outsider",
            user_id="user_outsider",
            season_id="27-28",
            match_id="27-28-match-01",
            player_id="gan-chenhao",
            content="不应写入",
            created_at=CREATED_AT,
            updated_at=CREATED_AT,
        )
    with pytest.raises(ValueError, match="社区互动权限"):
        toggle_rating_like(
            service_connection,
            user_id="user_outsider",
            rating_id="rating_other_season",
            created_at=CREATED_AT,
        )
    with pytest.raises(ValueError, match="社区互动权限"):
        toggle_comment_like(
            service_connection,
            user_id="user_outsider",
            comment_id="comment_existing",
            created_at=CREATED_AT,
        )


def test_submit_rating_still_uses_season_membership(
    service_connection: sqlite3.Connection,
) -> None:
    with pytest.raises(ValueError, match="评分权限"):
        submit_rating(
            service_connection,
            rating_id="rating_wrong_season",
            user_id="user_old_player",
            season_id="27-28",
            match_id="27-28-match-01",
            player_id="yao-hanrong",
            score=9.0,
            reason=None,
            created_at=CREATED_AT,
            updated_at=CREATED_AT,
        )

    rating_id = submit_rating(
        service_connection,
        rating_id="rating_allowed_season",
        user_id="user_old_player",
        season_id="25-26",
        match_id="25-26-regular-01",
        player_id="yao-hanrong",
        score=9.0,
        reason=None,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
    )
    assert rating_id == "rating_allowed_season"


@pytest.mark.parametrize("content", ["", "   ", "评" * 101])
def test_submit_comment_rejects_invalid_content(
    service_connection: sqlite3.Connection,
    content: str,
) -> None:
    with pytest.raises(ValueError):
        submit_comment(
            service_connection,
            comment_id="comment_invalid",
            user_id="user_old_player",
            season_id="27-28",
            match_id="27-28-match-01",
            player_id="gan-chenhao",
            content=content,
            created_at=CREATED_AT,
            updated_at=CREATED_AT,
        )


def test_like_requires_existing_target(service_connection: sqlite3.Connection) -> None:
    with pytest.raises(ValueError, match="评分不存在"):
        toggle_rating_like(
            service_connection,
            user_id="user_old_player",
            rating_id="missing_rating",
            created_at=CREATED_AT,
        )
    with pytest.raises(ValueError, match="评论不存在"):
        toggle_comment_like(
            service_connection,
            user_id="user_old_player",
            comment_id="missing_comment",
            created_at=CREATED_AT,
        )
