from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)
    session_id: str | None = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message must not be blank")
        return normalized


class AgentSource(BaseModel):
    id: str
    title: str
    source_type: str | None = None


class AgentChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[AgentSource] = Field(default_factory=list)
