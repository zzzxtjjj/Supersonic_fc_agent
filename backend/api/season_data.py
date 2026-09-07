import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEASON_DATA_ROOT = Path(
    os.getenv("SEASON_DATA_ROOT") or PROJECT_ROOT / "data" / "seasons"
)
SUPERSONIC_TEAM_ID = "supersonic"
_SEASON_PATTERN = re.compile(r"^\d{2}-\d{2}$")


class SeasonDataNotFound(FileNotFoundError):
    pass


def list_seasons() -> list[str]:
    """Return every valid season directory currently present in the data store."""

    if not SEASON_DATA_ROOT.is_dir():
        return []
    return [
        season_dir.name
        for season_dir in sorted(SEASON_DATA_ROOT.iterdir())
        if season_dir.is_dir() and _SEASON_PATTERN.fullmatch(season_dir.name)
    ]


def load_season_file(season: str, filename: str) -> dict[str, Any]:
    if not _SEASON_PATTERN.fullmatch(season):
        raise SeasonDataNotFound(f"Season not found: {season}")

    path = SEASON_DATA_ROOT / season / filename
    if not path.is_file():
        raise SeasonDataNotFound(f"Season data not found: {season}/{filename}")

    with path.open("r", encoding="utf-8") as source_file:
        return json.load(source_file)


def load_teams(season: str) -> list[dict[str, Any]]:
    return load_season_file(season, "teams.json").get("teams", [])


def load_matches(season: str) -> list[dict[str, Any]]:
    return load_season_file(season, "matches.json").get("matches", [])


def load_players(season: str) -> list[dict[str, Any]]:
    return load_season_file(season, "players.json").get("players", [])


def load_standings(season: str) -> list[dict[str, Any]]:
    return load_season_file(season, "standings.json").get("standings", [])


def team_map(season: str) -> dict[str, dict[str, Any]]:
    return {team["id"]: team for team in load_teams(season)}


def player_map(season: str) -> dict[str, dict[str, Any]]:
    return {player["id"]: player for player in load_players(season)}


def supersonic_goals_for(match: dict[str, Any]) -> int:
    if match["home_team_id"] == SUPERSONIC_TEAM_ID:
        return match["home_score"]
    if match["away_team_id"] == SUPERSONIC_TEAM_ID:
        return match["away_score"]
    raise ValueError(f"Match does not include Supersonic: {match['id']}")


def calculate_player_goal_totals(
    matches: list[dict[str, Any]],
) -> dict[str, int]:
    totals: dict[str, int] = defaultdict(int)
    for match in matches:
        for scorer in match.get("scorers", []):
            if scorer.get("type") != "player":
                continue
            player_id = scorer.get("player_id")
            if player_id:
                totals[player_id] += scorer["goals"]
    return dict(totals)


def calculate_match_player_stats(match: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Derive confirmed Supersonic goals and assists for one match."""

    totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"goals": 0, "assists": 0}
    )
    if "events" in match:
        for event in match.get("events") or []:
            if event.get("type") != "goal" or event.get("team_id") != SUPERSONIC_TEAM_ID:
                continue
            scorer_id = event.get("player_id") or event.get("scorer_player_id")
            if scorer_id:
                totals[scorer_id]["goals"] += 1
            assist_id = event.get("assist_player_id")
            if assist_id:
                totals[assist_id]["assists"] += 1
    else:
        for scorer in match.get("scorers", []):
            if scorer.get("type") != "player" or not scorer.get("player_id"):
                continue
            totals[scorer["player_id"]]["goals"] += int(scorer.get("goals", 0))
    return dict(totals)


def calculate_season_player_stats(
    matches: list[dict[str, Any]],
) -> dict[str, dict[str, int]]:
    """Aggregate confirmed match facts without inventing missing assists."""

    totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {"goals": 0, "assists": 0}
    )
    for match in matches:
        for player_id, facts in calculate_match_player_stats(match).items():
            totals[player_id]["goals"] += facts["goals"]
            totals[player_id]["assists"] += facts["assists"]
    return dict(totals)


def calculate_scorer_ranking(
    matches: list[dict[str, Any]],
    players: list[dict[str, Any]],
    *,
    show_all_scorers: bool = False,
) -> list[dict[str, Any]]:
    totals = calculate_player_goal_totals(matches)
    players_by_id = {player["id"]: player for player in players}
    ranking: list[dict[str, Any]] = []

    for player_id, goals in totals.items():
        player = players_by_id.get(player_id)
        if player is None:
            continue

        season_data = player.get("season_data", {})
        eligible = season_data.get("scorer_table_eligible", True)
        if not show_all_scorers and not eligible:
            continue

        ranking.append(
            {
                "player_id": player_id,
                "player_name": player["name"],
                "photo_url": player.get("photo_url"),
                "goals": goals,
                "scorer_table_eligible": eligible,
                "scorer_table_exclusion_reason": season_data.get(
                    "scorer_table_exclusion_reason"
                ),
            }
        )

    ranking.sort(key=lambda entry: (-entry["goals"], entry["player_id"]))

    previous_goals: int | None = None
    current_rank = 0
    for index, entry in enumerate(ranking, start=1):
        if entry["goals"] != previous_goals:
            current_rank = index
        entry["rank"] = current_rank
        previous_goals = entry["goals"]

    return ranking


def public_team(team: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": team["id"],
        "name": team["name"],
        "crest_url": team.get("crest_url"),
    }


def public_match(
    match: dict[str, Any],
    teams_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": match["id"],
        "season": match["season"],
        "competition": match["competition"],
        "stage": match["stage"],
        "round": match.get("round"),
        "leg": match.get("leg"),
        "date": match.get("date"),
        "home_team": public_team(teams_by_id[match["home_team_id"]]),
        "away_team": public_team(teams_by_id[match["away_team_id"]]),
        "home_score": match["home_score"],
        "away_score": match["away_score"],
        "scorers": match.get("scorers", []),
    }


def public_player(player: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": player["id"],
        "name": player["name"],
        "photo_url": player.get("photo_url"),
        "hometown": player.get("hometown"),
        "dominant_foot": player.get("dominant_foot"),
        "status": player.get("status"),
        "profile_complete": player.get("profile_complete", False),
    }


def public_player_season(
    player: dict[str, Any],
    season: str,
    goal_totals: dict[str, int],
    *,
    goals_available: bool = True,
) -> dict[str, Any]:
    season_data = player.get("season_data", {})
    return {
        "season": season,
        "number": season_data.get("number"),
        "position": season_data.get("position"),
        "appearances": season_data.get("appearances"),
        "goals": goal_totals.get(player["id"], 0) if goals_available else None,
        "assists": season_data.get("assists"),
        "technical_profile": season_data.get("technical_profile"),
        "is_captain": season_data.get("is_captain", False),
        "scorer_table_eligible": season_data.get("scorer_table_eligible", True),
        "scorer_table_exclusion_reason": season_data.get(
            "scorer_table_exclusion_reason"
        ),
    }


def find_match_record(match_id: str) -> dict[str, Any] | None:
    for season in list_seasons():
        matches = load_matches(season)
        match = next((item for item in matches if item["id"] == match_id), None)
        if match is not None:
            return match
    return None


def find_match(match_id: str) -> dict[str, Any] | None:
    match = find_match_record(match_id)
    if match is not None:
        return public_match(match, team_map(match["season"]))
    return None


def find_player(player_id: str) -> dict[str, Any] | None:
    identity: dict[str, Any] | None = None
    seasons: list[dict[str, Any]] = []

    for season in list_seasons():
        player = next(
            (item for item in load_players(season) if item["id"] == player_id),
            None,
        )
        if player is None:
            continue

        if identity is None:
            identity = public_player(player)
        matches = load_matches(season)
        goal_totals = calculate_player_goal_totals(matches)
        seasons.append(
            public_player_season(
                player,
                season,
                goal_totals,
                goals_available=bool(matches),
            )
        )

    if identity is None:
        return None
    return {"player": identity, "seasons": seasons}
