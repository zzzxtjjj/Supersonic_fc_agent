import time
from collections.abc import Callable, Iterable, Mapping
from typing import Any, TypeAlias

from evals.schemas import AgentOutput, EvalCase, EvalResult, EvaluationDecision


AgentCallable: TypeAlias = Callable[[str], str | Mapping[str, Any]]
Evaluator: TypeAlias = Callable[
    [EvalCase, AgentOutput],
    bool | EvaluationDecision | Mapping[str, Any] | None,
]

_PRIVATE_TRACE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "chain_of_thought",
    "reasoning",
    "reasoning_details",
    "reasoningdetails",
}


def _normalized_key(key: object) -> str:
    return str(key).strip().lower().replace("-", "_")


def _sanitize_trace_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _sanitize_trace_value(item)
            for key, item in value.items()
            if _normalized_key(key) not in _PRIVATE_TRACE_KEYS
        }
    if isinstance(value, list):
        return [_sanitize_trace_value(item) for item in value]
    return value


def _coerce_agent_output(raw_output: str | Mapping[str, Any]) -> AgentOutput:
    if isinstance(raw_output, str):
        return AgentOutput(final_answer=raw_output)

    if not isinstance(raw_output, Mapping):
        raise TypeError("agent_callable must return a string or mapping")

    final_answer = raw_output.get("final_answer")
    if not isinstance(final_answer, str):
        raise TypeError("agent mapping must contain a string final_answer")

    raw_trace = raw_output.get("trace")
    if raw_trace is None:
        raw_trace = []
    if not isinstance(raw_trace, list):
        raise TypeError("agent trace must be a list when provided")

    sanitized_trace = _sanitize_trace_value(raw_trace)
    return AgentOutput(final_answer=final_answer, trace=sanitized_trace)


def _base_metadata(case: EvalCase) -> dict[str, Any]:
    metadata = _sanitize_trace_value(dict(case.metadata))
    metadata["tags"] = list(case.tags)
    metadata["needs_manual_expected"] = case.needs_manual_expected
    return metadata


def _apply_evaluator(
    evaluator: Evaluator | None,
    case: EvalCase,
    agent_output: AgentOutput,
    metadata: dict[str, Any],
) -> str:
    if evaluator is None:
        return "not_evaluated"

    decision = evaluator(case, agent_output)
    if decision is None:
        return "not_evaluated"
    if isinstance(decision, bool):
        return "passed" if decision else "failed"

    parsed_decision = (
        decision
        if isinstance(decision, EvaluationDecision)
        else EvaluationDecision.model_validate(decision)
    )
    if parsed_decision.metadata:
        metadata["evaluator"] = _sanitize_trace_value(parsed_decision.metadata)
    return "passed" if parsed_decision.passed else "failed"


def run_suite(
    cases: Iterable[EvalCase],
    agent_callable: AgentCallable,
    evaluator: Evaluator | None = None,
) -> list[EvalResult]:
    """Run cases independently; one failed call never stops the remaining suite."""

    results: list[EvalResult] = []

    for case in cases:
        started_at = time.perf_counter()
        metadata = _base_metadata(case)
        agent_output: AgentOutput | None = None

        try:
            agent_output = _coerce_agent_output(agent_callable(case.question))
            status = _apply_evaluator(evaluator, case, agent_output, metadata)
            error = None
        except Exception as exc:  # Each case is an intentional isolation boundary.
            status = "error"
            error = f"{type(exc).__name__}: {exc}"

        latency_seconds = time.perf_counter() - started_at
        results.append(
            EvalResult(
                case_id=case.id,
                category=case.category,
                question=case.question,
                final_answer=(
                    agent_output.final_answer if agent_output is not None else None
                ),
                latency_seconds=latency_seconds,
                error=error,
                result=status,
                metadata=metadata,
                trace=agent_output.trace if agent_output is not None else [],
            )
        )

    return results
