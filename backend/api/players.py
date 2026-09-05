from fastapi import APIRouter, HTTPException, Query, status

from backend.api.season_data import (
    SeasonDataNotFound,
    calculate_player_goal_totals,
    find_player,
    load_matches,
    load_players,
    public_player,
    public_player_season,
)
from backend.schemas.player import (
    PlayerDetailResponse,
    PlayerListItem,
    PlayerListResponse,
)

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=PlayerListResponse)
async def list_players(
    season: str,
    player_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PlayerListResponse:
    """Return season players with media URLs and derived goal totals."""

    try:
        players = load_players(season)
        matches = load_matches(season)
        goal_totals = calculate_player_goal_totals(matches)
    except SeasonDataNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if player_status is not None:
        players = [player for player in players if player.get("status") == player_status]

    total = len(players)
    items = [
        PlayerListItem(
            player=public_player(player),
            season=public_player_season(
                player,
                season,
                goal_totals,
                goals_available=bool(matches),
            ),
        )
        for player in players[offset : offset + limit]
    ]
    return PlayerListResponse(season=season, items=items, total=total)


@router.get(
    "/{player_id}",
    response_model=PlayerDetailResponse,
    responses={404: {"description": "Player not found."}},
)
async def get_player(player_id: str) -> PlayerDetailResponse:
    player = find_player(player_id)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player not found: {player_id}",
        )
    return PlayerDetailResponse(**player)
