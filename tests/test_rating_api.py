import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api import ratings as ratings_api
from backend.api import season_data
from backend.main import app
from backend.rating_auth import (
    get_current_rating_user_optional,
    require_current_rating_user,
)
from backend.ratings.database import get_connection, init_database
from backend.ratings import database as ratings_database
from backend.ratings.repository import create_comment, create_or_update_rating


NOW = "2026-09-06T00:00:00+00:00"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _player(index: int) -> dict:
    return {
        "id": f"player-{index:02d}",
        "name": f"球员{index:02d}",
        "photo_url": f"/media/player-{index:02d}.png",
        "season_data": {"number": index, "position": None},
    }


def _create_season(
    root: Path,
    season: str,
    players: list[dict],
    match_id: str,
) -> None:
    season_dir = root / season
    _write_json(season_dir / "players.json", {"season": season, "players": players})
    _write_json(
        season_dir / "teams.json",
        {
            "season": season,
            "teams": [
                {
                    "id": "supersonic",
                    "name": "超音速",
                    "crest_url": "/supersonic-logo.png",
                },
                {"id": "opponent", "name": "对手", "crest_url": "/opponent.png"},
            ],
        },
    )
    _write_json(
        season_dir / "matches.json",
        {
            "season": season,
            "matches": [
                {
                    "id": match_id,
                    "season": season,
                    "competition": "超级联赛",
                    "stage": "regular",
                    "round": 1,
                    "date": "2026-09-01",
                    "home_team_id": "supersonic",
                    "away_team_id": "opponent",
                    "home_score": 2,
                    "away_score": 0,
                    "events": [
                        {
                            "type": "goal",
                            "team_id": "supersonic",
                            "player_id": players[0]["id"],
                            "assist_player_id": (
                                players[1]["id"] if len(players) > 1 else None
                            ),
                        },
                        {
                            "type": "goal",
                            "team_id": "supersonic",
                            "player_id": players[0]["id"],
                            "assist_player_id": None,
                        },
                    ],
                }
            ],
        },
    )
    _write_json(season_dir / "standings.json", {"season": season, "standings": []})


@pytest.fixture
def rating_workspace(tmp_path: Path, monkeypatch):
    season_root = tmp_path / "seasons"
    players = [_player(index) for index in range(1, 21)]
    _create_season(season_root, "25-26", players, "match-25")
    _create_season(
        season_root,
        "27-28",
        [_player(20)],
        "match-27",
    )
    monkeypatch.setattr(season_data, "SEASON_DATA_ROOT", season_root)

    database_path = tmp_path / "app.db"
    init_database(database_path)
    monkeypatch.setattr(ratings_database, "DB_PATH", database_path)
    connection = get_connection(database_path)
    connection.executemany(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        [
            ("user-01", "player-01", NOW),
            ("user-02", "player-02", NOW),
            ("user-03", "player-03", NOW),
            ("user-04", "player-04", NOW),
            ("user-outsider", "not-a-roster-player", NOW),
        ],
    )
    connection.executemany(
        "INSERT INTO season_rating_members (season_id, user_id) VALUES (?, ?)",
        [("25-26", f"user-{index:02d}") for index in range(1, 5)],
    )
    connection.commit()
    connection.close()

    def connection_override():
        current = get_connection(database_path)
        try:
            yield current
            current.commit()
        except Exception:
            current.rollback()
            raise
        finally:
            current.close()

    app.dependency_overrides[ratings_api.get_rating_connection] = connection_override
    yield {"database_path": database_path, "players": players}
    app.dependency_overrides.clear()


def _login_as(user_id: str) -> None:
    app.dependency_overrides[require_current_rating_user] = lambda: user_id
    app.dependency_overrides[get_current_rating_user_optional] = lambda: user_id


def _insert_rating(
    database_path: Path,
    *,
    rating_id: str,
    user_id: str,
    player_id: str = "player-01",
    score: float = 9.0,
) -> None:
    connection = get_connection(database_path)
    create_or_update_rating(
        connection,
        rating_id=rating_id,
        user_id=user_id,
        season_id="25-26",
        match_id="match-25",
        player_id=player_id,
        score=score,
        reason=f"理由 {rating_id}",
        created_at=NOW,
        updated_at=NOW,
    )
    connection.commit()
    connection.close()


def _insert_comment(
    database_path: Path,
    *,
    comment_id: str,
    user_id: str,
    updated_at: str,
    likes: tuple[str, ...] = (),
) -> None:
    connection = get_connection(database_path)
    create_comment(
        connection,
        comment_id=comment_id,
        user_id=user_id,
        season_id="25-26",
        match_id="match-25",
        player_id="player-01",
        content=comment_id,
        created_at=updated_at,
        updated_at=updated_at,
    )
    connection.executemany(
        "INSERT INTO comment_likes (user_id, comment_id, created_at) VALUES (?, ?, ?)",
        [(liker, comment_id, NOW) for liker in likes],
    )
    connection.commit()
    connection.close()


def test_public_rating_page_returns_all_twenty_official_players(rating_workspace) -> None:
    response = TestClient(app).get("/api/ratings/matches/match-25")

    assert response.status_code == 200
    body = response.json()
    assert len(body["players"]) == 20
    assert body["viewer"] == {
        "authenticated": False,
        "is_supersonic_player": False,
        "can_rate": False,
        "can_comment": False,
        "can_like": False,
    }
    assert body["players"][0]["name"] == "球员01"
    assert body["players"][0]["number"] == 1
    assert body["players"][0]["photo_url"] == "/media/player-01.png"
    assert body["players"][0]["match_facts"] == {"goals": 2, "assists": 0}
    assert body["players"][1]["match_facts"] == {"goals": 0, "assists": 1}
    assert body["players"][0]["rating"]["average"] is None
    assert body["players"][0]["rating"]["count"] == 0
    assert body["fan_mvp"] is None


def test_fan_mvp_requires_three_ratings(rating_workspace) -> None:
    path = rating_workspace["database_path"]
    _insert_rating(path, rating_id="r1", user_id="user-01", score=9.5)
    _insert_rating(path, rating_id="r2", user_id="user-02", score=9.0)
    assert TestClient(app).get("/api/ratings/matches/match-25").json()["fan_mvp"] is None

    _insert_rating(path, rating_id="r3", user_id="user-03", score=8.5)
    mvp = TestClient(app).get("/api/ratings/matches/match-25").json()["fan_mvp"]
    assert mvp["player_id"] == "player-01"
    assert mvp["average"] == 9.0
    assert mvp["rating_count"] == 3


def test_hot_comment_prefers_likes_then_newer_updated_at(rating_workspace) -> None:
    path = rating_workspace["database_path"]
    _insert_comment(
        path,
        comment_id="popular-old",
        user_id="user-01",
        updated_at="2026-01-01T00:00:00+00:00",
        likes=("user-02",),
    )
    _insert_comment(
        path,
        comment_id="popular-new",
        user_id="user-02",
        updated_at="2026-02-01T00:00:00+00:00",
        likes=("user-01",),
    )
    _insert_comment(
        path,
        comment_id="new-no-like",
        user_id="user-03",
        updated_at="2026-03-01T00:00:00+00:00",
    )

    page = TestClient(app).get("/api/ratings/matches/match-25").json()
    assert page["players"][0]["top_comment"]["id"] == "popular-new"


def test_hot_comment_with_all_zero_likes_is_latest(rating_workspace) -> None:
    path = rating_workspace["database_path"]
    _insert_comment(
        path,
        comment_id="old",
        user_id="user-01",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    _insert_comment(
        path,
        comment_id="new",
        user_id="user-02",
        updated_at="2026-02-01T00:00:00+00:00",
    )
    page = TestClient(app).get("/api/ratings/matches/match-25").json()
    assert page["players"][0]["top_comment"]["id"] == "new"


@pytest.mark.parametrize(
    ("method", "url", "body"),
    [
        ("put", "/api/ratings/matches/match-25/players/player-01", {"score": 9.5}),
        (
            "post",
            "/api/ratings/matches/match-25/players/player-01/comments",
            {"content": "评论"},
        ),
        ("post", "/api/ratings/missing/like", None),
        ("post", "/api/comments/missing/like", None),
    ],
)
def test_unauthenticated_writes_are_rejected(
    rating_workspace,
    method: str,
    url: str,
    body: dict | None,
) -> None:
    response = getattr(TestClient(app), method)(url, json=body)
    assert response.status_code == 401


def test_rating_body_rejects_forged_user_id(rating_workspace) -> None:
    _login_as("user-01")
    response = TestClient(app).put(
        "/api/ratings/matches/match-25/players/player-01",
        json={"score": 9.5, "user_id": "user-02"},
    )
    assert response.status_code == 422


def test_authenticated_member_can_rate_self_and_like_own_rating(rating_workspace) -> None:
    _login_as("user-01")
    client = TestClient(app)
    rating = client.put(
        "/api/ratings/matches/match-25/players/player-01",
        json={"score": 9.5, "reason": "自评"},
    )
    assert rating.status_code == 200
    liked = client.post(f"/api/ratings/{rating.json()['rating_id']}/like")
    assert liked.json() == {"liked": True, "like_count": 1}
    unliked = client.post(f"/api/ratings/{rating.json()['rating_id']}/like")
    assert unliked.json() == {"liked": False, "like_count": 0}


def test_authenticated_member_can_submit_one_tenth_score(rating_workspace) -> None:
    _login_as("user-01")
    response = TestClient(app).put(
        "/api/ratings/matches/match-25/players/player-01",
        json={"score": 8.1},
    )

    assert response.status_code == 200
    assert response.json()["score"] == 8.1


def test_old_player_can_comment_and_like_across_seasons(rating_workspace) -> None:
    _login_as("user-01")
    client = TestClient(app)
    comment = client.post(
        "/api/ratings/matches/match-27/players/player-20/comments",
        json={"content": "  跨赛季评论  "},
    )
    assert comment.status_code == 201
    assert comment.json()["content"] == "跨赛季评论"
    liked = client.post(f"/api/comments/{comment.json()['id']}/like")
    assert liked.json() == {"liked": True, "like_count": 1}


def test_non_rostered_registered_user_cannot_comment_or_like(rating_workspace) -> None:
    path = rating_workspace["database_path"]
    _insert_rating(path, rating_id="target", user_id="user-01")
    _login_as("user-outsider")
    client = TestClient(app)
    comment = client.post(
        "/api/ratings/matches/match-25/players/player-01/comments",
        json={"content": "不允许"},
    )
    like = client.post("/api/ratings/target/like")
    assert comment.status_code == 403
    assert like.status_code == 403
