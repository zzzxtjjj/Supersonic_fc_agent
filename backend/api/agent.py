from fastapi import APIRouter, HTTPException, status

from backend.schemas.agent import AgentChatRequest, AgentChatResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    responses={501: {"description": "LangGraph adapter is not connected yet."}},
)
async def chat(request: AgentChatRequest) -> AgentChatResponse:
    """Future boundary for the LangGraph agent; intentionally not connected."""

    del request
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Agent chat is a placeholder; no Agent or LangGraph workflow is connected.",
    )
