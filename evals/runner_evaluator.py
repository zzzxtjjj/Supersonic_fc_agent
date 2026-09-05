from evals.schemas import (
    AgentOutput,
    EvalCase,
    EvaluationDecision,
)

from evals.evaluator_v1 import evaluate_case


_SCORABLE_FIELDS = {
    "answer_contains",
    "tool_names",
    "workflow_outcome",
}


def build_expected(case: EvalCase, actual: dict) -> dict:
    expected = case.expected
    fields_set = expected.model_fields_set if expected is not None else set()

    return {
        "answer_contains": (
            expected.answer_contains
            if expected is not None and "answer_contains" in fields_set
            else []
        ),
        "tool_names": (
            expected.tool_names
            if expected is not None and "tool_names" in fields_set
            else actual["tool_names"]
        ),
        "workflow_outcome": (
            (expected.workflow_outcome or "")
            if expected is not None and "workflow_outcome" in fields_set
            else actual["workflow_outcome"]
        ),
    }


def extract_tool_names_from_trace(
    trace: list[dict],
) -> list[str]:
    tool_names = []

    for item in trace:
        if item.get("event") != "tool_call":
            continue

        tool_name = item.get("tool_name")

        if isinstance(tool_name, str) and tool_name:
            tool_names.append(tool_name)

    return tool_names


def extract_workflow_outcome_from_trace(
    trace: list[dict],
) -> str:
    for item in reversed(trace):
        if item.get("event") != "workflow_end":
            continue

        outcome = item.get("outcome")

        if isinstance(outcome, str) and outcome:
            return outcome

    return ""


def runner_evaluator(
    case: EvalCase,
    agent_output: AgentOutput,
) -> EvaluationDecision:
    actual = {
        "final_answer": agent_output.final_answer,

        "tool_names": extract_tool_names_from_trace(
            agent_output.trace
        ),

        "workflow_outcome": (
            extract_workflow_outcome_from_trace(
                agent_output.trace
            )
        ),
    }
    expected = build_expected(case, actual)
    evaluated_fields = (
        case.expected.model_fields_set & _SCORABLE_FIELDS
        if case.expected is not None
        else set()
    )

    result = evaluate_case(
        expected=expected,
        actual=actual,
    )

    return EvaluationDecision(
        passed=result["passed"],
        metadata={
            **result,
            "actual": actual,
            "evaluated_fields": sorted(evaluated_fields),
            "skipped_fields": sorted(_SCORABLE_FIELDS - evaluated_fields),
        },
    )
