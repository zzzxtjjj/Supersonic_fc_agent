import json
from collections.abc import Iterable, Mapping
from typing import Any, Literal, TypeAlias, TypedDict


class ToolCallTrace(TypedDict):
    event: Literal["tool_call"]
    tool_name: str


class ToolResultTrace(TypedDict):
    event: Literal["tool_result"]
    tool_name: str
    success: bool


class ExecutionVerificationTrace(TypedDict):
    event: Literal["execution_verification"]
    status: Literal["passed", "failed"]


class EvidenceVerificationTrace(TypedDict):
    event: Literal["evidence_verification"]
    status: Literal["supported", "insufficient"]


class GroundingRecoveryTrace(TypedDict):
    event: Literal["grounding_recovery"]


class WorkflowEndTrace(TypedDict):
    event: Literal["workflow_end"]
    outcome: Literal["answer", "clarify", "abort", "unknown"]


TraceEvent: TypeAlias = (
    ToolCallTrace
    | ToolResultTrace
    | ExecutionVerificationTrace
    | EvidenceVerificationTrace
    | GroundingRecoveryTrace
    | WorkflowEndTrace
)


class EvalAgentResponse(TypedDict):
    final_answer: str
    trace: list[TraceEvent]


def _load_runtime() -> tuple[Any, str]:
    # Keep production Agent/RAG imports behind the explicitly invoked adapter.
    from agent.workflow.graph import graph
    from agent.workflow.run_graph import SYSTEM_PROMPT

    return graph, SYSTEM_PROMPT


def _initial_state(question: str, system_prompt: str) -> dict[str, Any]:
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "step": 0,
        "max_steps": 5,
        "retry_count": 0,
        "max_retries": 2,
        "grounding_retry_count": 0,
        "max_grounding_retries": 2,
        "final_answer": None,
        "verification_status": "pending",
        "verification_reason": None,
        "recovery_strategy": None,
        "evidence_status": "pending",
        "evidence_reason": None,
    }


def _latest_message(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        return None
    message = messages[-1]
    return message if isinstance(message, Mapping) else None


def _recent_tool_messages(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return []
    recent: list[Mapping[str, Any]] = []
    for message in reversed(messages):
        if not isinstance(message, Mapping) or message.get("role") != "tool":
            break
        recent.append(message)
    return list(reversed(recent))


def _tool_success(message: Mapping[str, Any]) -> bool:
    try:
        result = json.loads(message.get("content", ""))
    except (json.JSONDecodeError, TypeError):
        return False
    return isinstance(result, dict) and result.get("success") is True


def _extract_final_answer(state: Mapping[str, Any]) -> str:
    final_answer = state.get("final_answer")
    if isinstance(final_answer, str) and final_answer.strip():
        return final_answer
    messages = state.get("messages")
    if isinstance(messages, list):
        for message in reversed(messages):
            if not isinstance(message, Mapping) or message.get("role") != "assistant":
                continue
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content
    return "Agent 未生成可用的最终回答。"


def _stream_updates(graph: Any, state: dict[str, Any]) -> Iterable[Mapping[str, Any]]:
    return graph.stream(state, stream_mode="updates")


def run_agent_for_eval(question: str) -> EvalAgentResponse:
    """Run the existing graph and adapt real node updates to the eval trace contract."""

    graph, system_prompt = _load_runtime()
    state = _initial_state(question, system_prompt)
    trace: list[TraceEvent] = []
    tool_names_by_call_id: dict[str, str] = {}
    outcome: Literal["answer", "clarify", "abort", "unknown"] | None = None

    for update in _stream_updates(graph, state):
        if not isinstance(update, Mapping):
            continue
        for node_name, raw_payload in update.items():
            if not isinstance(raw_payload, Mapping):
                continue
            payload = dict(raw_payload)
            state.update(payload)

            if node_name == "llm_node":
                assistant_message = _latest_message(payload)
                tool_calls = (
                    assistant_message.get("tool_calls", [])
                    if assistant_message is not None
                    else []
                )
                if isinstance(tool_calls, list):
                    for tool_call in tool_calls:
                        if not isinstance(tool_call, Mapping):
                            continue
                        function = tool_call.get("function")
                        if not isinstance(function, Mapping):
                            continue
                        tool_name = function.get("name")
                        if not isinstance(tool_name, str) or not tool_name:
                            continue
                        call_id = tool_call.get("id")
                        if isinstance(call_id, str):
                            tool_names_by_call_id[call_id] = tool_name
                        trace.append({"event": "tool_call", "tool_name": tool_name})

            elif node_name == "tool_node":
                for tool_message in _recent_tool_messages(payload):
                    call_id = tool_message.get("tool_call_id")
                    tool_name = (
                        tool_names_by_call_id.get(call_id, "unknown_tool")
                        if isinstance(call_id, str)
                        else "unknown_tool"
                    )
                    trace.append(
                        {
                            "event": "tool_result",
                            "tool_name": tool_name,
                            "success": _tool_success(tool_message),
                        }
                    )

            elif node_name == "verify_tool_results_node":
                verification_status = payload.get("verification_status")
                if verification_status in {"passed", "failed"}:
                    trace.append(
                        {
                            "event": "execution_verification",
                            "status": verification_status,
                        }
                    )

            elif node_name == "verify_evidence_node":
                evidence_status = payload.get("evidence_status")
                if evidence_status in {"supported", "insufficient"}:
                    trace.append(
                        {
                            "event": "evidence_verification",
                            "status": evidence_status,
                        }
                    )

            elif node_name == "grounding_recovery_node":
                trace.append({"event": "grounding_recovery"})

            elif node_name in {"clarify_node", "evidence_insufficient_node"}:
                outcome = "clarify"

            elif node_name == "abort_node":
                outcome = "abort"

    final_answer = _extract_final_answer(state)
    if outcome is None:
        outcome = (
            "unknown"
            if final_answer == "Agent 未生成可用的最终回答。"
            else "answer"
        )
    trace.append({"event": "workflow_end", "outcome": outcome})
    return {"final_answer": final_answer, "trace": trace}
