import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import auth, data_write
from backend.api import season_data
from backend.main import app


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "local-test-password"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def admin_workspace(tmp_path: Path, monkeypatch):
    season_root = tmp_path / "seasons"
    season_dir = season_root / "25-26"
    _write_json(
        season_dir / "players.json",
        {
            "season": "25-26",
            "players": [
                {
                    "id": "player-one",
                    "name": "球员一",
                    "custom_identity_field": "keep-me",
                    "season_data": {"number": 1, "position": "前锋"},
                },
                {
                    "id": "player-two",
                    "name": "球员二",
                    "season_data": {"number": 2, "position": "中场"},
                },
            ],
        },
    )
    _write_json(
        season_dir / "teams.json",
        {
            "season": "25-26",
            "teams": [
                {"id": "supersonic", "name": "超音速", "crest_url": "/s.png"},
                {"id": "opponent", "name": "对手", "crest_url": "/o.png"},
            ],
        },
    )
    _write_json(
        season_dir / "matches.json",
        {
            "season": "25-26",
            "assist_data_complete": False,
            "lineup_data_complete": False,
            "matches": [],
        },
    )
    _write_json(season_dir / "standings.json", {"season": "25-26", "standings": []})
    monkeypatch.setattr(season_data, "SEASON_DATA_ROOT", season_root)
    monkeypatch.setenv("ADMIN_USERNAME", ADMIN_USERNAME)
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", auth.hash_password(ADMIN_PASSWORD))
    monkeypatch.setenv("SESSION_SECRET", "test-secret-that-is-definitely-over-32-characters")
    monkeypatch.setenv("APP_ENV", "development")
    auth.clear_sessions_for_tests()
    yield {"root": season_root, "season_dir": season_dir}
    auth.clear_sessions_for_tests()


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/admin/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200


def _match_payload(match_id: str = "new-match") -> dict:
    return {
        "id": match_id,
        "competition": "超级联赛",
        "stage": "regular",
        "round": 1,
        "date": "2026-09-01",
        "home_team_id": "supersonic",
        "away_team_id": "opponent",
        "home_score": 3,
        "away_score": 1,
        "captain_player_id": "player-one",
        "goalkeeper_player_id": "player-two",
        "events": [
            {
                "type": "goal",
                "team_id": "supersonic",
                "scorer_player_id": "player-one",
                "assist_player_id": "player-two",
            },
            {
                "type": "goal",
                "team_id": "supersonic",
                "scorer_player_id": "player-one",
                "assist_player_id": None,
            },
            {
                "type": "own_goal",
                "team_id": "supersonic",
                "player_id": None,
            },
        ],
    }


@pytest.mark.parametrize(
    ("method", "url", "body"),
    [
        ("post", "/api/admin/seasons", {"season_id": "27-28"}),
        (
            "post",
            "/api/admin/seasons/25-26/players",
            {"id": "new-player", "name": "新球员"},
        ),
        (
            "patch",
            "/api/admin/seasons/25-26/players/player-one",
            {"name": "新名"},
        ),
        ("post", "/api/admin/seasons/25-26/matches", _match_payload()),
        (
            "put",
            "/api/admin/seasons/25-26/matches/new-match",
            _match_payload(),
        ),
    ],
)
def test_all_admin_writes_require_login(admin_workspace, method, url, body) -> None:
    response = getattr(TestClient(app), method)(url, json=body)
    assert response.status_code == 401


def test_admin_can_create_season_without_invented_teams(admin_workspace) -> None:
    client = TestClient(app)
    _login(client)
    response = client.post("/api/admin/seasons", json={"season_id": "27-28"})
    assert response.status_code == 201
    root = admin_workspace["root"] / "27-28"
    assert set(response.json()["created_files"]) == {
        "players.json",
        "matches.json",
        "teams.json",
        "standings.json",
    }
    assert json.loads((root / "teams.json").read_text(encoding="utf-8"))["teams"] == []
    assert client.post("/api/admin/seasons", json={"season_id": "27-28"}).status_code == 409


def test_admin_can_create_and_patch_player_preserving_unknown_fields(admin_workspace) -> None:
    client = TestClient(app)
    _login(client)
    created = client.post(
        "/api/admin/seasons/25-26/players",
        json={
            "id": "new-player",
            "name": "新球员",
            "season_data": {"number": 8, "position": None},
            "future_field": {"known_later": True},
        },
    )
    assert created.status_code == 201
    patched = client.patch(
        "/api/admin/seasons/25-26/players/new-player",
        json={"season_data": {"number": 9}},
    )
    assert patched.status_code == 200
    assert patched.json()["season_data"] == {"number": 9, "position": None}
    assert patched.json()["future_field"] == {"known_later": True}


def test_admin_cannot_manually_write_derived_season_totals(admin_workspace) -> None:
    client = TestClient(app)
    _login(client)
    response = client.post(
        "/api/admin/seasons/25-26/players",
        json={
            "id": "manual-total",
            "name": "错误累计",
            "season_data": {"number": 10, "goals": 99, "assists": 99},
        },
    )
    assert response.status_code == 422


def test_admin_can_create_update_match_and_preview_event_stats(admin_workspace) -> None:
    client = TestClient(app)
    _login(client)
    created = client.post(
        "/api/admin/seasons/25-26/matches",
        json=_match_payload(),
    )
    assert created.status_code == 201, created.text
    assert created.json()["scorers"] == [
        {
            "type": "player",
            "player_id": "player-one",
            "player_name": "球员一",
            "goals": 2,
            "note": None,
        },
        {
            "type": "own_goal",
            "player_id": None,
            "player_name": None,
            "goals": 1,
            "note": None,
        },
    ]
    preview = client.get("/api/admin/seasons/25-26/stats-preview")
    assert preview.status_code == 200
    assert preview.json()["scorers"] == [
        {"player_id": "player-one", "name": "球员一", "goals": 2, "assists": None}
    ]
    assert preview.json()["assists"] == [
        {"player_id": "player-two", "name": "球员二", "goals": None, "assists": 1}
    ]
    public_assists = client.get("/api/stats/assists", params={"season": "25-26"})
    assert public_assists.status_code == 200
    assert public_assists.json()["items"] == [
        {
            "rank": 1,
            "player_id": "player-two",
            "player_name": "球员二",
            "assists": 1,
        }
    ]

    changed = _match_payload()
    changed["home_score"] = 2
    changed["events"] = changed["events"][:2]
    updated = client.put(
        "/api/admin/seasons/25-26/matches/new-match",
        json=changed,
    )
    assert updated.status_code == 200
    assert len(updated.json()["scorers"]) == 1


@pytest.mark.parametrize(
    ("field_path", "bad_value"),
    [
        (("captain_player_id",), "missing-player"),
        (("events", 0, "scorer_player_id"), "missing-player"),
        (("events", 0, "assist_player_id"), "missing-player"),
    ],
)
def test_admin_rejects_invalid_player_references(
    admin_workspace,
    field_path,
    bad_value,
) -> None:
    payload = _match_payload()
    target = payload
    for key in field_path[:-1]:
        target = target[key]
    target[field_path[-1]] = bad_value
    client = TestClient(app)
    _login(client)
    response = client.post("/api/admin/seasons/25-26/matches", json=payload)
    assert response.status_code == 422


def test_admin_rejects_score_event_mismatch(admin_workspace) -> None:
    payload = _match_payload()
    payload["home_score"] = 4
    client = TestClient(app)
    _login(client)
    response = client.post("/api/admin/seasons/25-26/matches", json=payload)
    assert response.status_code == 422
    assert "does not match" in response.json()["detail"]


@pytest.mark.parametrize(
    "event_change",
    [
        {"type": "invented_event"},
        {"team_id": "missing-team"},
    ],
)
def test_admin_rejects_invalid_event_type_or_team(admin_workspace, event_change) -> None:
    payload = _match_payload()
    payload["events"][0].update(event_change)
    client = TestClient(app)
    _login(client)
    response = client.post("/api/admin/seasons/25-26/matches", json=payload)
    assert response.status_code == 422


def test_atomic_json_failure_keeps_original_file(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "players.json"
    original = {"players": [{"id": "old"}]}
    _write_json(target, original)

    def fail_replace(source, destination):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(data_write.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated"):
        data_write.atomic_write_json(target, {"players": [{"id": "new"}]})

    assert json.loads(target.read_text(encoding="utf-8")) == original
    assert list(tmp_path.glob("*.tmp")) == []


def test_json_backups_are_bounded(admin_workspace) -> None:
    client = TestClient(app)
    _login(client)
    for index in range(7):
        response = client.patch(
            "/api/admin/seasons/25-26/players/player-one",
            json={"name": f"球员{index}"},
        )
        assert response.status_code == 200
    backups = list(
        (admin_workspace["root"].parent / "backups" / "25-26" / "players.json").glob(
            "*.json"
        )
    )
    assert len(backups) == 5
