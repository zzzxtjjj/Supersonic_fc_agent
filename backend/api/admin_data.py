from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.admin_data_service import (
    AdminDataConflict,
    AdminDataError,
    AdminDataNotFound,
    create_match,
    create_player,
    create_season,
    get_stats_preview,
    list_admin_matches,
    list_admin_players,
    list_admin_seasons,
    update_match,
    update_player,
)
from backend.auth import require_admin
from backend.schemas.admin_data import (
    AdminMatchListResponse,
    AdminMatchWrite,
    AdminPlayerCreate,
    AdminPlayerListResponse,
    AdminPlayerPatch,
    AdminStatsPreviewResponse,
    SeasonCreateRequest,
    SeasonCreateResponse,
    SeasonListResponse,
)


router = APIRouter(
    prefix="/admin",
    tags=["admin-data"],
    dependencies=[Depends(require_admin)],
)


def _http_error(exc: AdminDataError) -> HTTPException:
    if isinstance(exc, AdminDataNotFound):
        code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, AdminDataConflict):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return HTTPException(status_code=code, detail=str(exc))


@router.get("/seasons", response_model=SeasonListResponse)
async def get_seasons() -> SeasonListResponse:
    return SeasonListResponse(seasons=list_admin_seasons())


@router.post(
    "/seasons",
    response_model=SeasonCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_season(payload: SeasonCreateRequest) -> SeasonCreateResponse:
    try:
        created_files = create_season(
            payload.season_id,
            [team.model_dump() for team in payload.teams],
        )
    except AdminDataError as exc:
        raise _http_error(exc) from exc
    return SeasonCreateResponse(
        season_id=payload.season_id,
        created_files=created_files,
    )


@router.get(
    "/seasons/{season_id}/players",
    response_model=AdminPlayerListResponse,
)
async def get_players(season_id: str) -> AdminPlayerListResponse:
    try:
        players = list_admin_players(season_id)
    except AdminDataError as exc:
        raise _http_error(exc) from exc
    return AdminPlayerListResponse(season_id=season_id, players=players)


@router.post(
    "/seasons/{season_id}/players",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
)
async def post_player(
    season_id: str,
    payload: AdminPlayerCreate,
) -> dict[str, Any]:
    try:
        return create_player(season_id, payload.model_dump(exclude_unset=True))
    except AdminDataError as exc:
        raise _http_error(exc) from exc


@router.patch(
    "/seasons/{season_id}/players/{player_id}",
    response_model=dict[str, Any],
)
async def patch_player(
    season_id: str,
    player_id: str,
    payload: AdminPlayerPatch,
) -> dict[str, Any]:
    try:
        return update_player(
            season_id,
            player_id,
            payload.model_dump(exclude_unset=True),
        )
    except AdminDataError as exc:
        raise _http_error(exc) from exc


@router.get(
    "/seasons/{season_id}/matches",
    response_model=AdminMatchListResponse,
)
async def get_matches(season_id: str) -> AdminMatchListResponse:
    try:
        matches = list_admin_matches(season_id)
    except AdminDataError as exc:
        raise _http_error(exc) from exc
    return AdminMatchListResponse(season_id=season_id, matches=matches)


@router.post(
    "/seasons/{season_id}/matches",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
)
async def post_match(
    season_id: str,
    payload: AdminMatchWrite,
) -> dict[str, Any]:
    try:
        return create_match(
            season_id,
            payload.model_dump(exclude_unset=True),
        )
    except AdminDataError as exc:
        raise _http_error(exc) from exc


@router.put(
    "/seasons/{season_id}/matches/{match_id}",
    response_model=dict[str, Any],
)
async def put_match(
    season_id: str,
    match_id: str,
    payload: AdminMatchWrite,
) -> dict[str, Any]:
    try:
        return update_match(
            season_id,
            match_id,
            payload.model_dump(exclude_unset=True),
        )
    except AdminDataError as exc:
        raise _http_error(exc) from exc


@router.get(
    "/seasons/{season_id}/stats-preview",
    response_model=AdminStatsPreviewResponse,
)
async def stats_preview(season_id: str) -> AdminStatsPreviewResponse:
    try:
        return AdminStatsPreviewResponse(**get_stats_preview(season_id))
    except AdminDataError as exc:
        raise _http_error(exc) from exc
