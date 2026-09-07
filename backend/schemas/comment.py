from pydantic import BaseModel, ConfigDict, Field


class CommentCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(max_length=100)


class CommunityAuthor(BaseModel):
    player_id: str
    name: str
    photo_url: str | None = None


class CommentResponse(BaseModel):
    id: str
    author: CommunityAuthor
    content: str
    like_count: int
    liked_by_me: bool
    created_at: str
    updated_at: str


class CommentListResponse(BaseModel):
    comments: list[CommentResponse] = Field(default_factory=list)


class LikeToggleResponse(BaseModel):
    liked: bool
    like_count: int
