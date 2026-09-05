import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool

from agent.workflow.run_graph import run_graph_agent
from backend.schemas.agent import AgentChatRequest, AgentChatResponse

router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)

SAFE_AGENT_ERROR = "AI 助手暂时无法完成请求，请稍后重试。"


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    response_model_exclude_none=True,
    responses={503: {"description": "The Agent is temporarily unavailable."}},
)
async def chat(request: AgentChatRequest) -> AgentChatResponse:
    """Run the existing product LangGraph Agent without exposing internal state."""

    try:
        answer = await run_in_threadpool(run_graph_agent, request.message)
    except Exception:
        logger.exception("Supersonic FC Agent request failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=SAFE_AGENT_ERROR,
        ) from None

    if not isinstance(answer, str) or not answer.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=SAFE_AGENT_ERROR,
        )

    return AgentChatResponse(
        answer=answer.strip(),
        session_id=request.session_id or str(uuid4()),
        sources=[],
    )
