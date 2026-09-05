from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GalleryItem(BaseModel):
    id: str
    url: str
    type: Literal["player", "team_group", "team"]
    original_name: str
    season: str | None = None
    player_ids: list[str] = Field(default_factory=list)
    team_id: str | None = None
    title: str | None = None
    caption: str | None = None
    date: str | None = None
    sort_order: int | None = None
    created_at: str


class GalleryListResponse(BaseModel):
    items: list[GalleryItem] = Field(default_factory=list)
    total: int = 0


class GalleryUploadResponse(BaseModel):
    status: str
    items: list[GalleryItem]


class GalleryDeleteResponse(BaseModel):
    status: str
    id: str


class GalleryMetadataUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    caption: str | None = None
    date: str | None = None
    sort_order: int | None = None


class MediaPlayerOption(BaseModel):
    id: str
    name: str
    photo_url: str | None = None


class MediaTeamOption(BaseModel):
    id: str
    name: str


class MediaOptionsResponse(BaseModel):
    season: str
    players: list[MediaPlayerOption] = Field(default_factory=list)
    teams: list[MediaTeamOption] = Field(default_factory=list)


class PlayerAvatarUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    season: str
    player_id: str
    media_id: str


class PlayerAvatarResponse(BaseModel):
    status: str
    season: str
    player_id: str
    media_id: str
    photo_url: str
