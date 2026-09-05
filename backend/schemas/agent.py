from pydantic import BaseModel, ConfigDict, Field


class AgentChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)
    session_id: str | None = None


class AgentSource(BaseModel):
    id: str
    title: str
    source_type: str | None = None


class ToolTraceItem(BaseModel):
    """Optional operational trace; never contains model reasoning or secrets."""

    tool_name: str
    status: str


class AgentChatResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[AgentSource] = Field(default_factory=list)
    tool_trace: list[ToolTraceItem] | None = None
