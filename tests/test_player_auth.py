import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import auth
from backend.api import season_data
from backend.main import app
from backend.ratings import database as ratings_database
from backend.ratings.database import get_connection, init_database


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin-password"
PLAYER_PASSWORD = "player-password"
NOW = "2026-09-06T00:00:00+00:00"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def auth_workspace(tmp_path: Path, monkeypatch):
    season_root = tmp_path / "seasons"
    season_dir = season_root / "25-26"
    players = [
        {
            "id": "player-one",
            "name": "球员一",
            "photo_url": "/media/official-one.png",
            "season_data": {"number": 1},
        },
        {
            "id": "player-two",
            "name": "球员二",
            "photo_url": None,
            "season_data": {"number": 2},
        },
    ]
    _write_json(season_dir / "players.json", {"season": "25-26", "players": players})
    _write_json(
        season_dir / "teams.json",
        {
            "season": "25-26",
            "teams": [
                {"id": "supersonic", "name": "超音速", "crest_url": "/s.png"},
                {"id": "opponent", "name": "对手", "crest_url": None},
            ],
        },
    )
    _write_json(
        season_dir / "matches.json",
        {
            "season": "25-26",
            "matches": [
                {
                    "id": "match-one",
                    "season": "25-26",
                    "competition": "联赛",
                    "stage": "regular",
                    "round": 1,
                    "date": "2026-09-01",
                    "home_team_id": "supersonic",
                    "away_team_id": "opponent",
                    "home_score": 0,
                    "away_score": 0,
                    "events": [],
                }
            ],
        },
    )
    _write_json(season_dir / "standings.json", {"season": "25-26", "standings": []})

    database_path = tmp_path / "app.db"
    init_database(database_path)
    connection = get_connection(database_path)
    connection.executemany(
        "INSERT INTO users (id, player_id, created_at) VALUES (?, ?, ?)",
        [
            ("user-player-one", "player-one", NOW),
            ("user-player-two", "player-two", NOW),
            ("user-outsider", "outside-player", NOW),
        ],
    )
    connection.execute(
        "INSERT INTO season_rating_members (season_id, user_id) VALUES (?, ?)",
        ("25-26", "user-player-one"),
    )
    connection.commit()
    connection.close()

    monkeypatch.setattr(season_data, "SEASON_DATA_ROOT", season_root)
    monkeypatch.setattr(ratings_database, "DB_PATH", database_path)
    monkeypatch.setenv("ADMIN_USERNAME", ADMIN_USERNAME)
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", auth.hash_password(ADMIN_PASSWORD))
    monkeypatch.setenv("SESSION_SECRET", "a-test-admin-session-secret-longer-than-32-chars")
    monkeypatch.setenv("APP_ENV", "development")
    auth.clear_sessions_for_tests()
    app.dependency_overrides.clear()
    yield {"database_path": database_path}
    app.dependency_overrides.clear()
    auth.clear_sessions_for_tests()


def _admin_login(client: TestClient) -> None:
    response = client.post(
        "/api/admin/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200


def _invite(client: TestClient, player_id: str = "player-one") -> str:
    _admin_login(client)
    response = client.post(f"/api/admin/player-invites/{player_id}")
    assert response.status_code == 200, response.text
    return response.json()["invite_code"]


def _activate(client: TestClient, player_id: str = "player-one") -> str:
    code = _invite(client, player_id)
    response = client.post(
        "/api/player-auth/activate",
        json={"invite_code": code, "password": PLAYER_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return code


def _login_player(client: TestClient, player_id: str = "player-one") -> None:
    response = client.post(
        "/api/player-auth/login",
        json={"player_id": player_id, "password": PLAYER_PASSWORD},
    )
    assert response.status_code == 200, response.text


def test_admin_can_generate_one_time_hashed_invite(auth_workspace) -> None:
    client = TestClient(app)
    code = _invite(client)
    body = client.post("/api/admin/player-invites/player-two").json()
    assert body["player_id"] == "player-two"
    assert body["invite_code"] != code
    assert body["expires_at"]

    connection = get_connection(auth_workspace["database_path"])
    stored = connection.execute(
        "SELECT code_hash FROM player_invites WHERE user_id = ?",
        ("user-player-one",),
    ).fetchone()[0]
    connection.close()
    assert stored != code
    assert code not in stored


def test_non_admin_cannot_generate_invite(auth_workspace) -> None:
    response = TestClient(app).post("/api/admin/player-invites/player-one")
    assert response.status_code == 401


def test_admin_cannot_invite_missing_official_player(auth_workspace) -> None:
    client = TestClient(app)
    _admin_login(client)
    response = client.post("/api/admin/player-invites/missing-player")
    assert response.status_code == 404


def test_invite_activates_correct_user_and_cannot_be_reused(auth_workspace) -> None:
    client = TestClient(app)
    code = _activate(client)
    again = client.post(
        "/api/player-auth/activate",
        json={"invite_code": code, "password": "another-password"},
    )
    assert again.status_code == 409

    connection = get_connection(auth_workspace["database_path"])
    row = connection.execute(
        "SELECT user_id, password_hash FROM user_credentials"
    ).fetchone()
    connection.close()
    assert row[0] == "user-player-one"
    assert row[1] != PLAYER_PASSWORD
    assert PLAYER_PASSWORD not in row[1]


def test_invalid_and_expired_invites_fail(auth_workspace) -> None:
    client = TestClient(app)
    invalid = client.post(
        "/api/player-auth/activate",
        json={"invite_code": "not-valid", "password": PLAYER_PASSWORD},
    )
    assert invalid.status_code == 400

    code = _invite(client)
    connection = get_connection(auth_workspace["database_path"])
    connection.execute(
        "UPDATE player_invites SET expires_at = ? WHERE used_at IS NULL",
        ("2000-01-01T00:00:00+00:00",),
    )
    connection.commit()
    connection.close()
    expired = client.post(
        "/api/player-auth/activate",
        json={"invite_code": code, "password": PLAYER_PASSWORD},
    )
    assert expired.status_code == 400


def test_correct_password_login_sets_httponly_player_cookie(auth_workspace) -> None:
    client = TestClient(app)
    _activate(client)
    response = client.post(
        "/api/player-auth/login",
        json={"player_id": "player-one", "password": PLAYER_PASSWORD},
    )
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "supersonic_player_session=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "user-player-one" not in cookie

    connection = get_connection(auth_workspace["database_path"])
    stored = connection.execute("SELECT token_hash FROM player_sessions").fetchone()[0]
    connection.close()
    assert client.cookies.get("supersonic_player_session") not in stored


def test_wrong_password_and_unactivated_account_cannot_login(auth_workspace) -> None:
    client = TestClient(app)
    _activate(client)
    wrong = client.post(
        "/api/player-auth/login",
        json={"player_id": "player-one", "password": "wrong-password"},
    )
    unactivated = client.post(
        "/api/player-auth/login",
        json={"player_id": "player-two", "password": PLAYER_PASSWORD},
    )
    assert wrong.status_code == 401
    assert unactivated.status_code == 403


def test_me_uses_official_player_name_and_photo(auth_workspace) -> None:
    client = TestClient(app)
    _activate(client)
    _login_player(client)
    response = client.get("/api/player-auth/me")
    assert response.status_code == 200
    assert response.json() == {
        "authenticated": True,
        "user": {
            "id": "user-player-one",
            "player_id": "player-one",
            "name": "球员一",
            "photo_url": "/media/official-one.png",
        },
        "is_supersonic_player": True,
    }


def test_logout_invalidates_server_session(auth_workspace) -> None:
    client = TestClient(app)
    _activate(client)
    _login_player(client)
    assert client.get("/api/player-auth/me").status_code == 200
    assert client.post("/api/player-auth/logout").json() == {"authenticated": False}
    assert client.get("/api/player-auth/me").status_code == 401


def test_player_session_can_write_rating_but_body_user_id_is_rejected(
    auth_workspace,
) -> None:
    client = TestClient(app)
    _activate(client)
    _login_player(client)
    forged = client.put(
        "/api/ratings/matches/match-one/players/player-one",
        json={"score": 9.5, "user_id": "user-player-two"},
    )
    assert forged.status_code == 422
    response = client.put(
        "/api/ratings/matches/match-one/players/player-one",
        json={"score": 9.5, "reason": "自评"},
    )
    assert response.status_code == 200
    connection = get_connection(auth_workspace["database_path"])
    stored_user = connection.execute("SELECT user_id FROM ratings").fetchone()[0]
    connection.close()
    assert stored_user == "user-player-one"


def test_no_player_session_still_cannot_write_rating(auth_workspace) -> None:
    response = TestClient(app).put(
        "/api/ratings/matches/match-one/players/player-one",
        json={"score": 9.5},
    )
    assert response.status_code == 401


def test_admin_session_cannot_replace_player_session(auth_workspace) -> None:
    client = TestClient(app)
    _admin_login(client)
    response = client.put(
        "/api/ratings/matches/match-one/players/player-one",
        json={"score": 9.5},
    )
    assert response.status_code == 401


def test_player_session_cannot_access_admin_api(auth_workspace) -> None:
    setup_client = TestClient(app)
    _activate(setup_client)
    player_client = TestClient(app)
    _login_player(player_client)
    assert player_client.get("/api/admin/seasons").status_code == 401


def test_rating_membership_rule_still_applies(auth_workspace) -> None:
    client = TestClient(app)
    _activate(client, "player-two")
    _login_player(client, "player-two")
    response = client.put(
        "/api/ratings/matches/match-one/players/player-two",
        json={"score": 8.0},
    )
    assert response.status_code == 403


def test_authenticated_rostered_player_can_use_community(auth_workspace) -> None:
    client = TestClient(app)
    _activate(client, "player-two")
    _login_player(client, "player-two")
    response = client.post(
        "/api/ratings/matches/match-one/players/player-two/comments",
        json={"content": "球队评论"},
    )
    assert response.status_code == 201


def test_registered_non_roster_user_session_is_not_community_authorized(
    auth_workspace,
) -> None:
    # Credentials and session cannot normally be issued through the invite API
    # for this user; inserting them here isolates the business authorization rule.
    connection = get_connection(auth_workspace["database_path"])
    connection.execute(
        """
        INSERT INTO user_credentials (user_id, password_hash, activated_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        ("user-outsider", auth.hash_password(PLAYER_PASSWORD), NOW, NOW),
    )
    connection.commit()
    connection.close()
    client = TestClient(app)
    _login_player(client, "outside-player")
    response = client.post(
        "/api/ratings/matches/match-one/players/player-one/comments",
        json={"content": "不应通过"},
    )
    assert response.status_code == 403
