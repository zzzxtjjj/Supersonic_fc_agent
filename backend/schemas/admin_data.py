from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AdminTeamInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    crest_url: str | None = None


class SeasonCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    season_id: str = Field(pattern=r"^\d{2}-\d{2}$")
    teams: list[AdminTeamInput] = Field(default_factory=list)


class SeasonListResponse(BaseModel):
    seasons: list[str] = Field(default_factory=list)


class SeasonCreateResponse(BaseModel):
    season_id: str
    created_files: list[str]


class AdminPlayerCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    aliases: list[str] | None = None
    photo_url: str | None = None
    season_data: dict[str, Any] | None = None


class AdminPlayerPatch(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str | None = None
    aliases: list[str] | None = None
    photo_url: str | None = None
    season_data: dict[str, Any] | None = None
    departure: dict[str, Any] | None = None
    transfer: dict[str, Any] | list[dict[str, Any]] | None = None
    career_milestones: list[dict[str, Any]] | None = None


class AdminPlayerListResponse(BaseModel):
    season_id: str
    players: list[dict[str, Any]] = Field(default_factory=list)


class AdminMatchEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    team_id: str | None = None
    player_id: str | None = None
    scorer_player_id: str | None = None
    assist_player_id: str | None = None
    forced_by_player_id: str | None = None
    player_in_id: str | None = None
    player_out_id: str | None = None
    minute: int | None = Field(default=None, ge=0)
    note: str | None = None


class AdminMatchWrite(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    season: str | None = None
    competition: str = Field(min_length=1)
    stage: str = Field(min_length=1)
    round: int | None = Field(default=None, ge=1)
    leg: int | None = Field(default=None, ge=1)
    date: str | None = None
    home_team_id: str = Field(min_length=1)
    away_team_id: str = Field(min_length=1)
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    captain_player_id: str | None = None
    goalkeeper_player_id: str | None = None
    events: list[AdminMatchEvent] | None = None


class AdminMatchListResponse(BaseModel):
    season_id: str
    matches: list[dict[str, Any]] = Field(default_factory=list)


class StatsPreviewEntry(BaseModel):
    player_id: str
    name: str
    goals: int | None = None
    assists: int | None = None


class AdminStatsPreviewResponse(BaseModel):
    season_id: str
    scorers: list[StatsPreviewEntry] = Field(default_factory=list)
    assists: list[StatsPreviewEntry] = Field(default_factory=list)
