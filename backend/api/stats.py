from fastapi import APIRouter, HTTPException, status

from backend.api.season_data import (
    SeasonDataNotFound,
    calculate_season_player_stats,
    calculate_scorer_ranking,
    load_matches,
    load_players,
    load_standings,
    team_map,
)
from backend.schemas.stats import AssistsResponse, ScorersResponse, StandingsResponse

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/standings", response_model=StandingsResponse)
async def get_standings(season: str) -> StandingsResponse:
    """Return the human-maintained official table without inferred fields."""

    try:
        standings = load_standings(season)
        teams_by_id = team_map(season)
    except SeasonDataNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    items = [
        {
            **row,
            "team_name": teams_by_id[row["team_id"]]["name"],
            "crest_url": teams_by_id[row["team_id"]].get("crest_url"),
        }
        for row in standings
    ]
    return StandingsResponse(season=season, items=items)


@router.get("/scorers", response_model=ScorersResponse)
async def get_scorers(
    season: str,
    show_all_scorers: bool = False,
) -> ScorersResponse:
    """Derive the scorer table from match events; never stores a second copy."""

    try:
        ranking = calculate_scorer_ranking(
            load_matches(season),
            load_players(season),
            show_all_scorers=show_all_scorers,
        )
    except SeasonDataNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return ScorersResponse(
        season=season,
        show_all_scorers=show_all_scorers,
        items=ranking,
    )


@router.get("/assists", response_model=AssistsResponse)
async def get_assists(season: str) -> AssistsResponse:
    """Derive confirmed assists from match events without filling unknown assists."""

    try:
        matches = load_matches(season)
        players = load_players(season)
    except SeasonDataNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    totals = calculate_season_player_stats(matches)
    players_by_id = {player["id"]: player for player in players}
    ranked = [
        {
            "player_id": player_id,
            "player_name": players_by_id[player_id]["name"],
            "assists": values["assists"],
        }
        for player_id, values in totals.items()
        if values["assists"] > 0 and player_id in players_by_id
    ]
    ranked.sort(key=lambda item: (-item["assists"], item["player_id"]))
    return AssistsResponse(
        season=season,
        items=[{"rank": index, **item} for index, item in enumerate(ranked, 1)],
    )
