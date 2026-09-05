from pathlib import Path

from backend.main import _allowed_origins
from backend.prepare_runtime_storage import prepare_runtime_storage


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_env_example_declares_required_names_without_real_credentials() -> None:
    values: dict[str, str] = {}
    for raw_line in (PROJECT_ROOT / ".env.example").read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value

    assert set(values) == {
        "OPENROUTER_API_KEY",
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD_HASH",
        "SESSION_SECRET",
        "APP_ENV",
        "FRONTEND_ORIGIN",
        "SERVE_FRONTEND",
        "FRONTEND_DIST",
        "SEASON_DATA_ROOT",
        "MEDIA_DATA_ROOT",
        "MEDIA_UPLOAD_ROOT",
    }
    assert values["OPENROUTER_API_KEY"] == ""
    assert values["ADMIN_PASSWORD_HASH"] == ""
    assert values["SESSION_SECRET"] == ""
    assert values["FRONTEND_ORIGIN"] == ""
    assert values["SERVE_FRONTEND"] == "false"
    assert values["FRONTEND_DIST"] == ""
    assert values["SEASON_DATA_ROOT"] == ""
    assert values["MEDIA_DATA_ROOT"] == ""
    assert values["MEDIA_UPLOAD_ROOT"] == ""


def test_health_endpoint_is_cheap_and_available() -> None:
    from fastapi.testclient import TestClient

    from backend.main import app

    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_production_cors_never_defaults_to_wildcard(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("FRONTEND_ORIGIN", raising=False)
    assert _allowed_origins() == []

    monkeypatch.setenv("FRONTEND_ORIGIN", "https://example.test/")
    assert _allowed_origins() == ["https://example.test"]


def test_runtime_storage_initializes_persistent_directories(
    tmp_path: Path,
    monkeypatch,
) -> None:
    seasons_root = tmp_path / "seasons"
    media_root = tmp_path / "media"
    uploads_root = tmp_path / "uploads"
    monkeypatch.setenv("SEASON_DATA_ROOT", str(seasons_root))
    monkeypatch.setenv("MEDIA_DATA_ROOT", str(media_root))
    monkeypatch.setenv("MEDIA_UPLOAD_ROOT", str(uploads_root))

    prepare_runtime_storage()

    players = __import__("json").loads(
        (seasons_root / "25-26" / "players.json").read_text(encoding="utf-8")
    )["players"]
    teams = __import__("json").loads(
        (seasons_root / "25-26" / "teams.json").read_text(encoding="utf-8")
    )["teams"]
    assert all(not str(player.get("photo_url") or "").startswith("/media/") for player in players)
    assert all(not str(team.get("crest_url") or "").startswith("/media/") for team in teams)
    assert next(team for team in teams if team["id"] == "supersonic")["crest_url"] == "/supersonic-logo.png"
    assert (media_root / "gallery.json").read_text(encoding="utf-8") == "[]\n"
    assert uploads_root.is_dir()
