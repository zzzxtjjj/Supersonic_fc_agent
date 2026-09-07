import copy
import json
import re
import threading
from pathlib import Path
from typing import Any

from backend.api import season_data
from backend.api.season_data import (
    SUPERSONIC_TEAM_ID,
    calculate_season_player_stats,
    load_matches,
    load_players,
    load_teams,
)
from backend.data_write import atomic_write_json


_SEASON_PATTERN = re.compile(r"^\d{2}-\d{2}$")
_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_EVENT_TYPES = {
    "goal",
    "own_goal",
    "substitution",
    "yellow_card",
    "red_card",
}
_write_lock = threading.Lock()


class AdminDataError(ValueError):
    pass


class AdminDataNotFound(AdminDataError):
    pass


class AdminDataConflict(AdminDataError):
    pass


def _root() -> Path:
    return season_data.SEASON_DATA_ROOT


def _backups_root() -> Path:
    return _root().parent / "backups"


def _season_dir(season_id: str) -> Path:
    if not _SEASON_PATTERN.fullmatch(season_id):
        raise AdminDataError("Invalid season id; expected XX-XX.")
    path = _root() / season_id
    if not path.is_dir():
        raise AdminDataNotFound(f"Season not found: {season_id}")
    return path


def _read_payload(path: Path, collection_key: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdminDataError(f"Invalid official data file: {path.name}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get(collection_key), list):
        raise AdminDataError(f"Invalid official data collection: {path.name}")
    return payload


def _write_payload(path: Path, payload: dict[str, Any], collection_key: str) -> None:
    def validate(value: Any) -> None:
        if not isinstance(value, dict) or not isinstance(value.get(collection_key), list):
            raise AdminDataError(f"Invalid official data collection: {path.name}")

    atomic_write_json(
        path,
        payload,
        validator=validate,
        backup_root=_backups_root(),
        max_backups=5,
    )


def list_admin_seasons() -> list[str]:
    return season_data.list_seasons()


def create_season(season_id: str, teams: list[dict[str, Any]]) -> list[str]:
    if not _SEASON_PATTERN.fullmatch(season_id):
        raise AdminDataError("Invalid season id; expected XX-XX.")
    if len({team["id"] for team in teams}) != len(teams):
        raise AdminDataError("Team ids must be unique.")
    target = _root() / season_id
    with _write_lock:
        if target.exists():
            raise AdminDataConflict(f"Season already exists: {season_id}")
        target.mkdir(parents=True)
        payloads = {
            "players.json": {"season": season_id, "players": []},
            "matches.json": {
                "season": season_id,
                "assist_data_complete": False,
                "lineup_data_complete": False,
                "matches": [],
            },
            "teams.json": {"season": season_id, "teams": teams},
            "standings.json": {"season": season_id, "standings": []},
        }
        for filename, payload in payloads.items():
            atomic_write_json(target / filename, payload)
    return list(payloads)


def list_admin_players(season_id: str) -> list[dict[str, Any]]:
    _season_dir(season_id)
    return load_players(season_id)


def _validate_player_write(player: dict[str, Any]) -> None:
    player_id = player.get("id")
    if not isinstance(player_id, str) or not _IDENTIFIER_PATTERN.fullmatch(player_id):
        raise AdminDataError("Invalid player id.")
    if not isinstance(player.get("name"), str) or not player["name"].strip():
        raise AdminDataError("Player name is required.")
    season_fields = player.get("season_data") or {}
    if not isinstance(season_fields, dict):
        raise AdminDataError("season_data must be an object.")
    forbidden = {"goals", "assists"}.intersection(season_fields)
    if forbidden:
        raise AdminDataError(
            "Season goal and assist totals are derived from match events."
        )


def create_player(season_id: str, player: dict[str, Any]) -> dict[str, Any]:
    _validate_player_write(player)
    path = _season_dir(season_id) / "players.json"
    with _write_lock:
        payload = _read_payload(path, "players")
        if any(item["id"] == player["id"] for item in payload["players"]):
            raise AdminDataConflict(f"Player already exists: {player['id']}")
        payload["players"].append(copy.deepcopy(player))
        _write_payload(path, payload, "players")
    return player


def _deep_merge(original: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(original)
    for key, value in changes.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def update_player(
    season_id: str,
    player_id: str,
    changes: dict[str, Any],
) -> dict[str, Any]:
    if "id" in changes:
        raise AdminDataError("Player id cannot be changed.")
    path = _season_dir(season_id) / "players.json"
    with _write_lock:
        payload = _read_payload(path, "players")
        index = next(
            (i for i, item in enumerate(payload["players"]) if item["id"] == player_id),
            None,
        )
        if index is None:
            raise AdminDataNotFound(f"Player not found: {player_id}")
        updated = _deep_merge(payload["players"][index], changes)
        _validate_player_write(updated)
        payload["players"][index] = updated
        _write_payload(path, payload, "players")
    return updated


def list_admin_matches(season_id: str) -> list[dict[str, Any]]:
    _season_dir(season_id)
    return load_matches(season_id)


def _require_player_id(player_ids: set[str], value: Any, label: str) -> None:
    if value is not None and value not in player_ids:
        raise AdminDataError(f"Invalid {label}: {value}")


def _normalize_events(
    events: list[dict[str, Any]],
    *,
    player_ids: set[str],
    team_ids: set[str],
) -> list[dict[str, Any]]:
    normalized_events: list[dict[str, Any]] = []
    for raw_event in events:
        event = copy.deepcopy(raw_event)
        event_type = event.get("type")
        if event_type not in _EVENT_TYPES:
            raise AdminDataError(f"Unsupported match event type: {event_type}")
        event_team_id = event.get("team_id")
        if event_team_id is not None and event_team_id not in team_ids:
            raise AdminDataError(f"Invalid event team_id: {event_team_id}")
        if event_type in {"goal", "own_goal"} and event_team_id is None:
            raise AdminDataError(f"{event_type} event requires team_id.")
        scorer_id = event.get("player_id") or event.get("scorer_player_id")
        if (
            event.get("player_id")
            and event.get("scorer_player_id")
            and event["player_id"] != event["scorer_player_id"]
        ):
            raise AdminDataError("player_id and scorer_player_id disagree.")
        if event_type == "goal" and event.get("team_id") == SUPERSONIC_TEAM_ID:
            if scorer_id is None:
                raise AdminDataError("Supersonic goal requires a scorer_player_id.")
        _require_player_id(player_ids, scorer_id, "scorer_player_id")
        _require_player_id(player_ids, event.get("assist_player_id"), "assist_player_id")
        _require_player_id(player_ids, event.get("forced_by_player_id"), "forced_by_player_id")
        _require_player_id(player_ids, event.get("player_in_id"), "player_in_id")
        _require_player_id(player_ids, event.get("player_out_id"), "player_out_id")
        if scorer_id is not None:
            event["player_id"] = scorer_id
        event.pop("scorer_player_id", None)
        normalized_events.append(event)
    return normalized_events


def _supersonic_score(match: dict[str, Any]) -> int:
    if match["home_team_id"] == SUPERSONIC_TEAM_ID:
        return int(match["home_score"])
    if match["away_team_id"] == SUPERSONIC_TEAM_ID:
        return int(match["away_score"])
    raise AdminDataError("Match must include Supersonic.")


def _derive_scorers(
    events: list[dict[str, Any]],
    players_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    player_goals: dict[str, int] = {}
    own_goals = 0
    for event in events:
        if event.get("team_id") != SUPERSONIC_TEAM_ID:
            continue
        if event.get("type") == "goal":
            player_id = event["player_id"]
            player_goals[player_id] = player_goals.get(player_id, 0) + 1
        elif event.get("type") == "own_goal":
            own_goals += 1
    scorers = [
        {
            "type": "player",
            "player_id": player_id,
            "player_name": players_by_id[player_id]["name"],
            "goals": goals,
            "note": None,
        }
        for player_id, goals in player_goals.items()
    ]
    if own_goals:
        scorers.append(
            {
                "type": "own_goal",
                "player_id": None,
                "player_name": None,
                "goals": own_goals,
                "note": None,
            }
        )
    return scorers


def _validate_and_normalize_match(
    season_id: str,
    match: dict[str, Any],
    *,
    creating: bool,
) -> dict[str, Any]:
    match = copy.deepcopy(match)
    if match.get("season") not in (None, season_id):
        raise AdminDataError("Match season does not match the endpoint season.")
    match["season"] = season_id
    if match.get("home_team_id") == match.get("away_team_id"):
        raise AdminDataError("Home and away teams must differ.")
    if int(match.get("home_score", -1)) < 0 or int(match.get("away_score", -1)) < 0:
        raise AdminDataError("Scores must be non-negative.")

    players = load_players(season_id)
    teams = load_teams(season_id)
    players_by_id = {player["id"]: player for player in players}
    player_ids = set(players_by_id)
    team_ids = {team["id"] for team in teams}
    if match.get("home_team_id") not in team_ids or match.get("away_team_id") not in team_ids:
        raise AdminDataError("Home and away team ids must exist in teams.json.")
    _require_player_id(player_ids, match.get("captain_player_id"), "captain_player_id")
    _require_player_id(
        player_ids,
        match.get("goalkeeper_player_id"),
        "goalkeeper_player_id",
    )

    has_events = "events" in match and match["events"] is not None
    if creating and not has_events and _supersonic_score(match) > 0:
        raise AdminDataError("A scored match must include its goal events.")
    if has_events:
        events = _normalize_events(
            match.get("events") or [],
            player_ids=player_ids,
            team_ids=team_ids,
        )
        event_goals = sum(
            1
            for event in events
            if event.get("team_id") == SUPERSONIC_TEAM_ID
            and event.get("type") in {"goal", "own_goal"}
        )
        if event_goals != _supersonic_score(match):
            raise AdminDataError(
                "Supersonic score does not match goal and own-goal events."
            )
        match["events"] = events
        match["scorers"] = _derive_scorers(events, players_by_id)
    return match


def create_match(season_id: str, match: dict[str, Any]) -> dict[str, Any]:
    path = _season_dir(season_id) / "matches.json"
    with _write_lock:
        existing_match = season_data.find_match_record(match["id"])
        if existing_match is not None:
            raise AdminDataConflict(f"Match already exists: {match['id']}")
        payload = _read_payload(path, "matches")
        normalized = _validate_and_normalize_match(season_id, match, creating=True)
        payload["matches"].append(normalized)
        _write_payload(path, payload, "matches")
    return normalized


def update_match(
    season_id: str,
    match_id: str,
    match: dict[str, Any],
) -> dict[str, Any]:
    if match.get("id") != match_id:
        raise AdminDataError("Match id cannot be changed.")
    path = _season_dir(season_id) / "matches.json"
    with _write_lock:
        payload = _read_payload(path, "matches")
        index = next(
            (i for i, item in enumerate(payload["matches"]) if item["id"] == match_id),
            None,
        )
        if index is None:
            raise AdminDataNotFound(f"Match not found: {match_id}")
        merged = _deep_merge(payload["matches"][index], match)
        normalized = _validate_and_normalize_match(season_id, merged, creating=False)
        payload["matches"][index] = normalized
        _write_payload(path, payload, "matches")
    return normalized


def get_stats_preview(season_id: str) -> dict[str, Any]:
    _season_dir(season_id)
    players = load_players(season_id)
    totals = calculate_season_player_stats(load_matches(season_id))
    players_by_id = {player["id"]: player for player in players}
    scorers = [
        {
            "player_id": player_id,
            "name": players_by_id[player_id]["name"],
            "goals": facts["goals"],
        }
        for player_id, facts in totals.items()
        if facts["goals"] > 0 and player_id in players_by_id
    ]
    assists = [
        {
            "player_id": player_id,
            "name": players_by_id[player_id]["name"],
            "assists": facts["assists"],
        }
        for player_id, facts in totals.items()
        if facts["assists"] > 0 and player_id in players_by_id
    ]
    scorers.sort(key=lambda item: (-item["goals"], item["player_id"]))
    assists.sort(key=lambda item: (-item["assists"], item["player_id"]))
    return {"season_id": season_id, "scorers": scorers, "assists": assists}
