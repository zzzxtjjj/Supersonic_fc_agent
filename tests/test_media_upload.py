import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import auth, media_storage
from backend.main import app


PNG_BYTES = b"\x89PNG\r\n\x1a\nlocal-test-image"
ADMIN_USERNAME = "local-admin"
ADMIN_PASSWORD = "correct horse battery staple"
ADMIN_PASSWORD_HASH = auth.hash_password(ADMIN_PASSWORD)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def media_workspace(tmp_path, monkeypatch) -> dict[str, Path]:
    season_root = tmp_path / "seasons"
    season_dir = season_root / "25-26"
    player_path = season_dir / "players.json"
    team_path = season_dir / "teams.json"
    match_path = season_dir / "matches.json"
    media_root = tmp_path / "uploads"
    media_index = tmp_path / "media" / "gallery.json"

    _write_json(
        player_path,
        {
            "season": "25-26",
            "players": [
                {"id": "player-one", "name": "球员一", "photo_url": None},
                {"id": "player-two", "name": "球员二", "photo_url": None},
            ],
        },
    )
    _write_json(
        team_path,
        {
            "season": "25-26",
            "teams": [
                {"id": "supersonic", "name": "超音速", "crest_url": "/supersonic-logo.png"},
                {"id": "opponent", "name": "对手", "crest_url": None},
            ],
        },
    )
    _write_json(
        match_path,
        {
            "season": "25-26",
            "matches": [
                {
                    "id": "match-one",
                    "season": "25-26",
                    "home_team_id": "supersonic",
                    "away_team_id": "opponent",
                    "home_score": 4,
                    "away_score": 1,
                }
            ],
        },
    )
    _write_json(media_index, [])

    monkeypatch.setattr(media_storage, "SEASON_DATA_ROOT", season_root)
    monkeypatch.setattr(media_storage, "MEDIA_DATA_ROOT", media_index.parent)
    monkeypatch.setattr(media_storage, "MEDIA_INDEX_PATH", media_index)
    monkeypatch.setattr(media_storage, "MEDIA_ROOT", media_root)

    return {
        "player_path": player_path,
        "team_path": team_path,
        "media_root": media_root,
        "media_index": media_index,
    }


@pytest.fixture(autouse=True)
def admin_environment(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", ADMIN_USERNAME)
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", ADMIN_PASSWORD_HASH)
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret-with-at-least-32-characters")
    monkeypatch.setenv("APP_ENV", "development")
    auth.clear_sessions_for_tests()
    yield
    auth.clear_sessions_for_tests()


def _image(filename: str, content: bytes = PNG_BYTES):
    return (filename, content, "image/png")


def _login(client: TestClient):
    return client.post(
        "/api/admin/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )


def test_public_gallery_is_available_without_login(media_workspace) -> None:
    with TestClient(app) as client:
        response = client.get("/api/gallery")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_media_options_only_return_players_and_teams(media_workspace) -> None:
    with TestClient(app) as client:
        response = client.get("/api/gallery/options", params={"season": "25-26"})

    assert response.status_code == 200
    assert set(response.json()) == {"season", "players", "teams"}


def test_upload_is_rejected_without_login(media_workspace) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/gallery/upload",
            files=[("files", _image("blocked.png"))],
            data={"category": "team_group"},
        )

    assert response.status_code == 401
    assert json.loads(media_workspace["media_index"].read_text(encoding="utf-8")) == []


def test_authenticated_non_admin_session_is_forbidden(media_workspace) -> None:
    with TestClient(app) as client:
        client.cookies.set(auth.SESSION_COOKIE_NAME, auth._create_session("viewer"))
        response = client.post(
            "/api/gallery/upload",
            files=[("files", _image("blocked-role.png"))],
            data={"category": "team_group"},
        )

    assert response.status_code == 403


def test_wrong_password_is_rejected(media_workspace) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/login",
            json={"username": ADMIN_USERNAME, "password": "wrong-password"},
        )

    assert response.status_code == 401


def test_correct_login_sets_private_session_cookie(media_workspace) -> None:
    with TestClient(app) as client:
        response = _login(client)
        me = client.get("/api/admin/me")

    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert me.json() == {"authenticated": True}
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert "max-age" not in cookie


def test_password_hash_and_production_cookie_security(media_workspace, monkeypatch) -> None:
    assert ADMIN_PASSWORD not in ADMIN_PASSWORD_HASH
    assert auth.verify_password(ADMIN_PASSWORD, ADMIN_PASSWORD_HASH)
    assert not auth.verify_password("wrong-password", ADMIN_PASSWORD_HASH)

    monkeypatch.setenv("APP_ENV", "production")
    with TestClient(app) as client:
        response = _login(client)

    assert response.status_code == 200
    assert "secure" in response.headers["set-cookie"].lower()


def test_tampered_session_cookie_is_rejected(media_workspace) -> None:
    with TestClient(app) as client:
        valid_cookie = auth.create_admin_session()
        client.cookies.set(auth.SESSION_COOKIE_NAME, f"{valid_cookie}tampered")
        response = client.post(
            "/api/gallery/upload",
            files=[("files", _image("tampered.png"))],
            data={"category": "team_group"},
        )

    assert response.status_code == 401


def test_single_team_group_upload_persists_after_list_refresh(media_workspace) -> None:
    with TestClient(app) as client:
        assert _login(client).status_code == 200
        response = client.post(
            "/api/gallery/upload",
            files=[("files", _image("team-photo.png"))],
            data={
                "category": "team_group",
                "season": "25-26",
                "title": "球队合照",
                "caption": "本地测试",
            },
        )
        assert response.status_code == 201
        item = response.json()["items"][0]
        assert item["url"].startswith("/media/team_group/media-")
        assert item["url"].endswith(".png")

        stored_path = media_workspace["media_root"] / item["url"].removeprefix(
            "/media/"
        )
        assert stored_path.read_bytes() == PNG_BYTES

        refreshed = client.get("/api/gallery")
        assert refreshed.status_code == 200
        assert refreshed.json()["total"] == 1
        assert refreshed.json()["items"][0]["id"] == item["id"]


def test_gallery_filters_by_season_category_and_player(media_workspace) -> None:
    with TestClient(app) as client:
        assert _login(client).status_code == 200
        personal = client.post(
            "/api/gallery/upload",
            files=[("files", _image("personal.png"))],
            data={
                "category": "player",
                "season": "25-26",
                "player_ids": json.dumps(["player-one"]),
            },
        )
        team_group = client.post(
            "/api/gallery/upload",
            files=[("files", _image("team-group.png"))],
            data={
                "category": "team_group",
                "season": "25-26",
            },
        )

        personal_list = client.get(
            "/api/gallery",
            params={
                "season": "25-26",
                "category": "player",
                "player_id": "player-one",
            },
        )
        team_group_list = client.get(
            "/api/gallery",
            params={"season": "25-26", "category": "team_group"},
        )

    assert personal.status_code == 201
    assert team_group.status_code == 201
    assert personal_list.json()["total"] == 1
    assert personal_list.json()["items"][0]["type"] == "player"
    assert team_group_list.json()["total"] == 1
    assert team_group_list.json()["items"][0]["type"] == "team_group"


def test_multiple_team_group_images_do_not_overwrite(media_workspace) -> None:
    with TestClient(app) as client:
        assert _login(client).status_code == 200
        response = client.post(
            "/api/gallery/upload",
            files=[
                ("files", _image("same-name.png", PNG_BYTES + b"-one")),
                ("files", _image("same-name.png", PNG_BYTES + b"-two")),
            ],
            data={
                "category": "team_group",
                "season": "25-26",
            },
        )

    assert response.status_code == 201
    items = response.json()["items"]
    assert len(items) == 2
    assert {item["type"] for item in items} == {"team_group"}
    assert len({item["url"] for item in items}) == 2
    stored_contents = {
        (
            media_workspace["media_root"]
            / item["url"].removeprefix("/media/")
        ).read_bytes()
        for item in items
    }
    assert stored_contents == {PNG_BYTES + b"-one", PNG_BYTES + b"-two"}


@pytest.mark.parametrize("removed_category", ["match", "gallery"])
def test_removed_photo_categories_are_rejected(
    media_workspace,
    removed_category,
) -> None:
    with TestClient(app) as client:
        assert _login(client).status_code == 200
        response = client.post(
            "/api/gallery/upload",
            files=[("files", _image(f"{removed_category}.png"))],
            data={"category": removed_category, "season": "25-26"},
        )

    assert response.status_code == 400
    assert "category" in response.json()["detail"].lower()


def test_player_images_bind_to_selected_players(media_workspace) -> None:
    with TestClient(app) as client:
        assert _login(client).status_code == 200
        response = client.post(
            "/api/gallery/upload",
            files=[
                ("files", _image("one.png")),
                ("files", _image("two.png")),
            ],
            data={
                "category": "player",
                "season": "25-26",
                "player_ids": json.dumps(["player-one", "player-two"]),
            },
        )

    assert response.status_code == 201
    items = response.json()["items"]
    players = json.loads(media_workspace["player_path"].read_text(encoding="utf-8"))[
        "players"
    ]
    assert players[0]["photo_url"] == items[0]["url"]
    assert players[1]["photo_url"] == items[1]["url"]


def test_team_crest_binds_without_overwriting_original_logo(media_workspace) -> None:
    with TestClient(app) as client:
        assert _login(client).status_code == 200
        response = client.post(
            "/api/gallery/upload",
            files=[("files", _image("new-crest.png"))],
            data={
                "category": "team",
                "season": "25-26",
                "team_id": "supersonic",
            },
        )

    assert response.status_code == 201
    item = response.json()["items"][0]
    teams = json.loads(media_workspace["team_path"].read_text(encoding="utf-8"))[
        "teams"
    ]
    assert teams[0]["crest_url"] == item["url"]
    assert item["url"] != "/supersonic-logo.png"


def test_non_image_file_is_rejected_without_metadata(media_workspace) -> None:
    with TestClient(app) as client:
        assert _login(client).status_code == 200
        response = client.post(
            "/api/gallery/upload",
            files=[("files", ("notes.txt", b"not an image", "text/plain"))],
            data={"category": "team_group", "season": "25-26"},
        )

    assert response.status_code == 400
    assert "image" in response.json()["detail"].lower()
    metadata = json.loads(media_workspace["media_index"].read_text(encoding="utf-8"))
    assert metadata == []


def test_admin_can_delete_uploaded_media(media_workspace) -> None:
    with TestClient(app) as client:
        assert _login(client).status_code == 200
        uploaded = client.post(
            "/api/gallery/upload",
            files=[("files", _image("delete-me.png"))],
            data={"category": "team_group", "season": "25-26"},
        ).json()["items"][0]
        stored_path = media_workspace["media_root"] / uploaded["url"].removeprefix(
            "/media/"
        )
        assert stored_path.is_file()

        deleted = client.delete(f"/api/gallery/{uploaded['id']}")

    assert deleted.status_code == 200
    assert deleted.json() == {"status": "deleted", "id": uploaded["id"]}
    assert not stored_path.exists()
    assert json.loads(media_workspace["media_index"].read_text(encoding="utf-8")) == []


def test_logout_revokes_upload_permission(media_workspace) -> None:
    with TestClient(app) as client:
        assert _login(client).status_code == 200
        assert client.post("/api/admin/logout").json() == {"authenticated": False}
        response = client.post(
            "/api/gallery/upload",
            files=[("files", _image("after-logout.png"))],
            data={"category": "team_group"},
        )

    assert response.status_code == 401


def test_public_user_cannot_set_player_photo(media_workspace) -> None:
    before = media_workspace["player_path"].read_text(encoding="utf-8")
    with TestClient(app) as client:
        response = client.post(
            "/api/gallery/upload",
            files=[("files", _image("player.png"))],
            data={
                "category": "player",
                "season": "25-26",
                "player_ids": json.dumps(["player-one"]),
            },
        )

    assert response.status_code == 401
    assert media_workspace["player_path"].read_text(encoding="utf-8") == before


def test_public_user_cannot_set_team_crest_or_patch_metadata(media_workspace) -> None:
    before = media_workspace["team_path"].read_text(encoding="utf-8")
    with TestClient(app) as client:
        crest_response = client.post(
            "/api/gallery/upload",
            files=[("files", _image("crest.png"))],
            data={
                "category": "team",
                "season": "25-26",
                "team_id": "supersonic",
            },
        )
        patch_response = client.patch(
            "/api/gallery/nonexistent",
            json={"caption": "unauthorized"},
        )

    assert crest_response.status_code == 401
    assert patch_response.status_code == 401
    assert media_workspace["team_path"].read_text(encoding="utf-8") == before
