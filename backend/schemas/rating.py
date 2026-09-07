from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.comment import CommentResponse, CommunityAuthor


class RatingSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0, le=10, multiple_of=0.1)
    reason: str | None = Field(default=None, max_length=100)


class RatingSubmitResponse(BaseModel):
    rating_id: str
    score: float
    reason: str | None
    average: float
    rating_count: int


class RatingReasonResponse(BaseModel):
    id: str
    author: CommunityAuthor
    score: float
    reason: str
    like_count: int
    liked_by_me: bool
    updated_at: str


class ViewerPermissions(BaseModel):
    authenticated: bool
    is_supersonic_player: bool
    can_rate: bool
    can_comment: bool
    can_like: bool


class RatingMatchTeam(BaseModel):
    id: str
    name: str
    crest_url: str | None = None


class RatingMatchSummary(BaseModel):
    id: str
    season_id: str
    competition: str
    round: int | None = None
    date: str | None = None
    home_team: RatingMatchTeam
    away_team: RatingMatchTeam
    home_score: int
    away_score: int


class MatchFacts(BaseModel):
    goals: int = 0
    assists: int = 0


class PlayerRatingAggregate(BaseModel):
    average: float | None = None
    count: int = 0
    my_score: float | None = None
    my_reason: str | None = None
    reasons: list[RatingReasonResponse] = Field(default_factory=list)


class RatingPagePlayer(BaseModel):
    player_id: str
    name: str
    number: int | None = None
    photo_url: str | None = None
    match_facts: MatchFacts
    rating: PlayerRatingAggregate
    top_comment: CommentResponse | None = None
    comment_count: int = 0


class FanMvpResponse(BaseModel):
    player_id: str
    name: str
    photo_url: str | None = None
    average: float
    rating_count: int


class RatingMatchPageResponse(BaseModel):
    match: RatingMatchSummary
    viewer: ViewerPermissions
    fan_mvp: FanMvpResponse | None = None
    players: list[RatingPagePlayer] = Field(default_factory=list)
