from pydantic import BaseModel, Field


class Player(BaseModel):
    id: str
    name: str
    photo_url: str | None = None
    hometown: str | None = None
    dominant_foot: str | None = None
    status: str | None = None
    profile_complete: bool = False


class PlayerSeason(BaseModel):
    season: str
    number: int | None = None
    position: str | None = None
    appearances: int | None = None
    goals: int | None = None
    assists: int | None = None
    technical_profile: str | None = None
    is_captain: bool = False
    scorer_table_eligible: bool = True
    scorer_table_exclusion_reason: str | None = None


class PlayerListItem(BaseModel):
    player: Player
    season: PlayerSeason


class PlayerListResponse(BaseModel):
    season: str
    items: list[PlayerListItem] = Field(default_factory=list)
    total: int = 0


class PlayerDetailResponse(BaseModel):
    player: Player
    seasons: list[PlayerSeason] = Field(default_factory=list)
