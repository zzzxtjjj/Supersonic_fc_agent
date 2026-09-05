from pydantic import BaseModel, Field


class StandingEntry(BaseModel):
    rank: int
    team_id: str
    team_name: str
    crest_url: str | None = None
    points: int
    goal_difference: int
    goals_for: int


class ScorerEntry(BaseModel):
    rank: int
    player_id: str
    player_name: str
    photo_url: str | None = None
    goals: int
    scorer_table_eligible: bool
    scorer_table_exclusion_reason: str | None = None


class AssistEntry(BaseModel):
    rank: int
    player_id: str
    player_name: str
    assists: int


class StandingsResponse(BaseModel):
    season: str
    items: list[StandingEntry] = Field(default_factory=list)


class ScorersResponse(BaseModel):
    season: str
    show_all_scorers: bool = False
    items: list[ScorerEntry] = Field(default_factory=list)


class AssistsResponse(BaseModel):
    season: str
    items: list[AssistEntry] = Field(default_factory=list)
