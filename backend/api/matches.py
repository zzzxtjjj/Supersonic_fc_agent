from fastapi import APIRouter, HTTPException, Query, status

from backend.api.season_data import (
    SeasonDataNotFound,
    find_match,
    load_matches,
    public_match,
    team_map,
)
from backend.schemas.match import MatchDetailResponse, MatchListResponse

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=MatchListResponse)
async def list_matches(
    season: str,
    stage: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> MatchListResponse:
    """Read a season's structured match feed from the canonical JSON files."""

    try:
        matches = load_matches(season)
        teams_by_id = team_map(season)
    except SeasonDataNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if stage is not None:
        matches = [match for match in matches if match["stage"] == stage]

    total = len(matches)
    items = [
        public_match(match, teams_by_id)
        for match in matches[offset : offset + limit]
    ]
    return MatchListResponse(season=season, items=items, total=total)


@router.get(
    "/{match_id}",
    response_model=MatchDetailResponse,
    responses={404: {"description": "Match not found."}},
)
async def get_match(match_id: str) -> MatchDetailResponse:
    match = find_match(match_id)
    if match is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match not found: {match_id}",
        )
    return MatchDetailResponse(match=match)
