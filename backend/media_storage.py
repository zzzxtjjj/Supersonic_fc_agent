import json
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEASON_DATA_ROOT = PROJECT_ROOT / "data" / "seasons"
MEDIA_DATA_ROOT = PROJECT_ROOT / "data" / "media"
MEDIA_INDEX_PATH = MEDIA_DATA_ROOT / "gallery.json"
MEDIA_ROOT = Path(__file__).resolve().parent / "static" / "uploads"

ALLOWED_CATEGORIES = {"player", "team_group", "team"}
MAX_FILE_SIZE = 10 * 1024 * 1024

_write_lock = threading.Lock()


class MediaValidationError(ValueError):
    pass


@dataclass(frozen=True)
class IncomingImage:
    filename: str
    content_type: str | None
    content: bytes


def ensure_storage() -> None:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    MEDIA_DATA_ROOT.mkdir(parents=True, exist_ok=True)
    if not MEDIA_INDEX_PATH.exists():
        _write_json(MEDIA_INDEX_PATH, [])


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as target_file:
        json.dump(payload, target_file, ensure_ascii=False, indent=2)
        target_file.write("\n")
    temporary_path.replace(path)


def _season_path(season: str, filename: str) -> Path:
    if not season or any(character not in "0123456789-" for character in season):
        raise MediaValidationError("Invalid season.")
    path = SEASON_DATA_ROOT / season / filename
    if not path.is_file():
        raise MediaValidationError(f"Season data not found: {season}/{filename}")
    return path


def _detect_extension(content: bytes) -> str | None:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    return None


def _validate_image(image: IncomingImage) -> str:
    if not image.filename:
        raise MediaValidationError("Every upload must have a filename.")
    if not image.content:
        raise MediaValidationError(f"Image is empty: {image.filename}")
    if len(image.content) > MAX_FILE_SIZE:
        raise MediaValidationError(
            f"Image exceeds the 10 MB limit: {image.filename}"
        )

    detected_extension = _detect_extension(image.content)
    if detected_extension is None:
        raise MediaValidationError(f"Unsupported or invalid image: {image.filename}")

    supplied_extension = Path(image.filename).suffix.lower()
    if supplied_extension == ".jpeg":
        supplied_extension = ".jpg"
    if supplied_extension != detected_extension:
        raise MediaValidationError(
            f"Image extension does not match its content: {image.filename}"
        )

    allowed_content_types = {
        ".png": {"image/png"},
        ".jpg": {"image/jpeg", "image/jpg"},
        ".webp": {"image/webp"},
    }
    if image.content_type not in allowed_content_types[detected_extension]:
        raise MediaValidationError(f"Unsupported image type: {image.filename}")
    return detected_extension


def _load_season_collection(season: str, filename: str, key: str) -> tuple[Path, dict]:
    path = _season_path(season, filename)
    payload = _read_json(path)
    if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
        raise MediaValidationError(f"Invalid season data: {season}/{filename}")
    return path, payload


def _validate_context(
    *,
    category: str,
    season: str | None,
    player_ids: list[str],
    team_id: str | None,
    file_count: int,
) -> None:
    if category not in ALLOWED_CATEGORIES:
        raise MediaValidationError(f"Unsupported category: {category}")

    if not season:
        raise MediaValidationError(f"Season is required for {category} uploads.")

    if category == "player":
        if len(player_ids) != file_count:
            raise MediaValidationError("Select one player for every player image.")
        _, payload = _load_season_collection(season or "", "players.json", "players")
        known_ids = {player["id"] for player in payload["players"]}
        unknown_ids = sorted(set(player_ids) - known_ids)
        if unknown_ids:
            raise MediaValidationError(f"Unknown player id: {', '.join(unknown_ids)}")

    if category == "team":
        if file_count != 1:
            raise MediaValidationError("Upload exactly one crest for a team.")
        if not team_id:
            raise MediaValidationError("Team is required for a team crest.")
        _, payload = _load_season_collection(season or "", "teams.json", "teams")
        if team_id not in {team["id"] for team in payload["teams"]}:
            raise MediaValidationError(f"Unknown team id: {team_id}")

    if category == "team_group" and player_ids:
        raise MediaValidationError("Team group photos cannot be assigned to players.")


def _update_player_photos(season: str, bindings: list[tuple[str, str]]) -> None:
    path, payload = _load_season_collection(season, "players.json", "players")
    urls_by_player = dict(bindings)
    for player in payload["players"]:
        if player["id"] in urls_by_player:
            player["photo_url"] = urls_by_player[player["id"]]
    _write_json(path, payload)


def _update_team_crest(season: str, team_id: str, url: str) -> None:
    path, payload = _load_season_collection(season, "teams.json", "teams")
    for team in payload["teams"]:
        if team["id"] == team_id:
            team["crest_url"] = url
            break
    _write_json(path, payload)


def store_media_batch(
    images: list[IncomingImage],
    *,
    category: str,
    season: str | None = None,
    player_ids: list[str] | None = None,
    team_id: str | None = None,
    title: str | None = None,
    caption: str | None = None,
    date: str | None = None,
    sort_order: int | None = None,
) -> list[dict[str, Any]]:
    if not images:
        raise MediaValidationError("Select at least one image.")

    normalized_player_ids = player_ids or []
    extensions = [_validate_image(image) for image in images]
    _validate_context(
        category=category,
        season=season,
        player_ids=normalized_player_ids,
        team_id=team_id,
        file_count=len(images),
    )

    category_root = MEDIA_ROOT / category
    category_root.mkdir(parents=True, exist_ok=True)
    created_paths: list[Path] = []
    items: list[dict[str, Any]] = []

    try:
        for index, (image, extension) in enumerate(zip(images, extensions, strict=True)):
            media_id = f"media-{uuid.uuid4().hex}"
            stored_filename = f"{media_id}{extension}"
            target_path = category_root / stored_filename
            target_path.write_bytes(image.content)
            created_paths.append(target_path)

            item_player_ids = (
                [normalized_player_ids[index]]
                if category == "player"
                else normalized_player_ids
            )
            items.append(
                {
                    "id": media_id,
                    "type": category,
                    "url": f"/media/{category}/{stored_filename}",
                    "original_name": Path(image.filename).name,
                    "season": season,
                    "player_ids": item_player_ids,
                    "team_id": team_id,
                    "title": title,
                    "caption": caption,
                    "date": date,
                    "sort_order": sort_order,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )

        with _write_lock:
            ensure_storage()
            current_items = _read_json(MEDIA_INDEX_PATH)
            if not isinstance(current_items, list):
                raise MediaValidationError("Media metadata index is invalid.")

            if category == "player":
                _update_player_photos(
                    season or "",
                    [
                        (item["player_ids"][0], item["url"])
                        for item in items
                    ],
                )
            elif category == "team":
                _update_team_crest(season or "", team_id or "", items[0]["url"])

            _write_json(MEDIA_INDEX_PATH, current_items + items)
    except Exception:
        for path in created_paths:
            path.unlink(missing_ok=True)
        raise

    return items


def list_media(
    *,
    season: str | None = None,
    player_id: str | None = None,
    category: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    ensure_storage()
    items = _read_json(MEDIA_INDEX_PATH)
    if not isinstance(items, list):
        raise MediaValidationError("Media metadata index is invalid.")
    if season is not None:
        items = [item for item in items if item.get("season") == season]
    if player_id is not None:
        items = [item for item in items if player_id in item.get("player_ids", [])]
    if category is not None:
        if category not in ALLOWED_CATEGORIES:
            raise MediaValidationError(f"Unsupported category: {category}")
        items = [item for item in items if item.get("type") == category]

    items.sort(
        key=lambda item: (
            item.get("sort_order") is None,
            item.get("sort_order") or 0,
            item.get("created_at") or "",
        )
    )
    return items[offset : offset + limit], len(items)


def update_media_metadata(
    media_id: str,
    changes: dict[str, Any],
) -> dict[str, Any]:
    allowed_fields = {"title", "caption", "date", "sort_order"}
    if not changes or not set(changes).issubset(allowed_fields):
        raise MediaValidationError("No supported metadata fields were supplied.")

    with _write_lock:
        ensure_storage()
        items = _read_json(MEDIA_INDEX_PATH)
        item = next((entry for entry in items if entry.get("id") == media_id), None)
        if item is None:
            raise MediaValidationError(f"Media item not found: {media_id}")
        item.update(changes)
        _write_json(MEDIA_INDEX_PATH, items)
    return item


def _clear_deleted_entity_binding(item: dict[str, Any]) -> None:
    season = item.get("season")
    url = item.get("url")
    if item.get("type") == "player" and season:
        path, payload = _load_season_collection(season, "players.json", "players")
        bound_ids = set(item.get("player_ids", []))
        changed = False
        for player in payload["players"]:
            if player["id"] in bound_ids and player.get("photo_url") == url:
                player["photo_url"] = None
                changed = True
        if changed:
            _write_json(path, payload)
    elif item.get("type") == "team" and season and item.get("team_id"):
        path, payload = _load_season_collection(season, "teams.json", "teams")
        changed = False
        for team in payload["teams"]:
            if team["id"] == item["team_id"] and team.get("crest_url") == url:
                team["crest_url"] = None
                changed = True
        if changed:
            _write_json(path, payload)


def delete_media(media_id: str) -> dict[str, Any]:
    with _write_lock:
        ensure_storage()
        items = _read_json(MEDIA_INDEX_PATH)
        item = next((entry for entry in items if entry.get("id") == media_id), None)
        if item is None:
            raise MediaValidationError(f"Media item not found: {media_id}")

        _clear_deleted_entity_binding(item)
        remaining_items = [entry for entry in items if entry.get("id") != media_id]
        _write_json(MEDIA_INDEX_PATH, remaining_items)

        url = item.get("url", "")
        expected_prefix = f"/media/{item.get('type')}/"
        if isinstance(url, str) and url.startswith(expected_prefix):
            filename = Path(url).name
            target = (MEDIA_ROOT / str(item.get("type")) / filename).resolve()
            if target.is_relative_to(MEDIA_ROOT.resolve()):
                target.unlink(missing_ok=True)
    return item


ensure_storage()
