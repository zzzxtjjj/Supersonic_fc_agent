import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from backend.api.season_data import (
    SeasonDataNotFound,
    load_players,
    load_teams,
)
from backend.auth import require_admin
from backend.media_storage import (
    MAX_FILE_SIZE,
    IncomingImage,
    MediaValidationError,
    delete_media,
    list_media,
    store_media_batch,
    update_media_metadata,
)
from backend.schemas.gallery import (
    GalleryDeleteResponse,
    GalleryItem,
    GalleryListResponse,
    GalleryMetadataUpdate,
    GalleryUploadResponse,
    MediaOptionsResponse,
)

router = APIRouter(prefix="/gallery", tags=["gallery"])


def _parse_player_ids(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="player_ids must be a JSON array.",
        ) from exc
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="player_ids must be a JSON array of player ids.",
        )
    return value


@router.get("/options", response_model=MediaOptionsResponse)
async def get_media_options(season: str) -> MediaOptionsResponse:
    """Return canonical season entities used by the upload form."""

    try:
        players = load_players(season)
        teams = load_teams(season)
    except SeasonDataNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return MediaOptionsResponse(
        season=season,
        players=[{"id": player["id"], "name": player["name"]} for player in players],
        teams=[{"id": team["id"], "name": team["name"]} for team in teams],
    )


@router.get("", response_model=GalleryListResponse)
async def list_gallery(
    season: str | None = None,
    player_id: str | None = None,
    category: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> GalleryListResponse:
    try:
        items, total = list_media(
            season=season,
            player_id=player_id,
            category=category,
            limit=limit,
            offset=offset,
        )
    except MediaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    return GalleryListResponse(items=items, total=total)


@router.post(
    "/upload",
    response_model=GalleryUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def upload_gallery_items(
    files: list[UploadFile] = File(...),
    category: str = Form(...),
    season: str | None = Form(default=None),
    player_ids: str | None = Form(default=None),
    team_id: str | None = Form(default=None),
    title: str | None = Form(default=None),
    caption: str | None = Form(default=None),
    date: str | None = Form(default=None),
    sort_order: int | None = Form(default=None),
) -> GalleryUploadResponse:
    """Persist one local upload batch and its canonical media metadata."""

    parsed_player_ids = _parse_player_ids(player_ids)
    images: list[IncomingImage] = []
    for upload in files:
        content = await upload.read(MAX_FILE_SIZE + 1)
        images.append(
            IncomingImage(
                filename=upload.filename or "",
                content_type=upload.content_type,
                content=content,
            )
        )

    try:
        items = store_media_batch(
            images,
            category=category,
            season=season,
            player_ids=parsed_player_ids,
            team_id=team_id,
            title=title,
            caption=caption,
            date=date,
            sort_order=sort_order,
        )
    except MediaValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return GalleryUploadResponse(status="uploaded", items=items)


@router.patch(
    "/{media_id}",
    response_model=GalleryItem,
    dependencies=[Depends(require_admin)],
)
async def patch_gallery_item(
    media_id: str,
    payload: GalleryMetadataUpdate,
) -> GalleryItem:
    try:
        item = update_media_metadata(
            media_id,
            payload.model_dump(include=payload.model_fields_set),
        )
    except MediaValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return GalleryItem(**item)


@router.delete(
    "/{media_id}",
    response_model=GalleryDeleteResponse,
    dependencies=[Depends(require_admin)],
)
async def delete_gallery_item(media_id: str) -> GalleryDeleteResponse:
    try:
        delete_media(media_id)
    except MediaValidationError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return GalleryDeleteResponse(status="deleted", id=media_id)
