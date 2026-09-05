import json
import os
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_SEASONS_ROOT = PROJECT_ROOT / "data" / "seasons"


def _configured_path(name: str, default: Path) -> Path:
    return Path(os.getenv(name) or default)


def _clear_unavailable_media_references(seasons_root: Path) -> None:
    for players_path in seasons_root.glob("*/players.json"):
        payload = json.loads(players_path.read_text(encoding="utf-8"))
        changed = False
        for player in payload.get("players", []):
            if str(player.get("photo_url") or "").startswith("/media/"):
                player["photo_url"] = None
                changed = True
        if changed:
            players_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

    for teams_path in seasons_root.glob("*/teams.json"):
        payload = json.loads(teams_path.read_text(encoding="utf-8"))
        changed = False
        for team in payload.get("teams", []):
            if str(team.get("crest_url") or "").startswith("/media/"):
                team["crest_url"] = None
                changed = True
        if changed:
            teams_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )


def prepare_runtime_storage() -> None:
    seasons_root = _configured_path("SEASON_DATA_ROOT", SEED_SEASONS_ROOT)
    media_data_root = _configured_path(
        "MEDIA_DATA_ROOT", PROJECT_ROOT / "data" / "media"
    )
    upload_root = _configured_path(
        "MEDIA_UPLOAD_ROOT", PROJECT_ROOT / "backend" / "static" / "uploads"
    )

    if seasons_root.resolve() != SEED_SEASONS_ROOT.resolve() and not seasons_root.exists():
        shutil.copytree(SEED_SEASONS_ROOT, seasons_root)
        _clear_unavailable_media_references(seasons_root)

    media_data_root.mkdir(parents=True, exist_ok=True)
    media_index = media_data_root / "gallery.json"
    if not media_index.exists():
        media_index.write_text("[]\n", encoding="utf-8")
    upload_root.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    prepare_runtime_storage()
