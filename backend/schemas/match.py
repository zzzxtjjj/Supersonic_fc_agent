from typing import Literal

from pydantic import BaseModel, Field


class TeamSummary(BaseModel):
    id: str
    name: str
    crest_url: str | None = None


class ScorerEvent(BaseModel):
    type: Literal["player", "own_goal"]
    goals: int = Field(ge=1)
    player_id: str | None = None
    player_name: str | None = None
    note: str | None = None


class Match(BaseModel):
    id: str
    season: str
    competition: str
    stage: Literal["regular", "playoff_semifinal"]
    round: int | None = None
    leg: int | None = None
    date: str | None = None
    home_team: TeamSummary
    away_team: TeamSummary
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    scorers: list[ScorerEvent] = Field(default_factory=list)


class MatchListResponse(BaseModel):
    season: str
    items: list[Match] = Field(default_factory=list)
    total: int = 0


class MatchDetailResponse(BaseModel):
    match: Match
