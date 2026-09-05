from evals.runner_evaluator import runner_evaluator
from evals.schemas import AgentOutput, EvalCase


def _case(expected: dict) -> EvalCase:
    return EvalCase.model_validate(
        {
            "id": "case",
            "category": "test",
            "question": "question",
            "expected": expected,
        }
    )


def _output(
    *,
    answer: str = "任意回答",
    tools: list[str] | None = None,
    outcome: str = "answer",
) -> AgentOutput:
    trace = [
        {"event": "tool_call", "tool_name": tool_name}
        for tool_name in (tools or [])
    ]
    trace.append({"event": "workflow_end", "outcome": outcome})
    return AgentOutput(final_answer=answer, trace=trace)


def test_omitted_workflow_outcome_is_not_scored() -> None:
    decision = runner_evaluator(
        _case(
            {
                "answer_contains": ["3"],
                "tool_names": ["get_player_goals"],
            }
        ),
        _output(
            answer="张谢童甲在25-26赛季进了3个球。",
            tools=["get_player_goals"],
            outcome="answer",
        ),
    )

    assert decision.passed is True
    assert "workflow_outcome" in decision.metadata["skipped_fields"]


def test_explicit_empty_tool_names_passes_when_no_tool_is_called() -> None:
    decision = runner_evaluator(
        _case({"tool_names": []}),
        _output(tools=[]),
    )

    assert decision.passed is True
    assert "tool_names" in decision.metadata["evaluated_fields"]


def test_explicit_empty_tool_names_fails_when_a_tool_is_called() -> None:
    decision = runner_evaluator(
        _case({"tool_names": []}),
        _output(tools=["search_team_knowledge"]),
    )

    assert decision.passed is False
    assert decision.metadata["tool_selection_passed"] is False


def test_explicit_clarify_outcome_is_scored() -> None:
    decision = runner_evaluator(
        _case({"workflow_outcome": "clarify"}),
        _output(tools=["get_player_goals"], outcome="clarify"),
    )

    assert decision.passed is True
    assert decision.metadata["evaluated_fields"] == ["workflow_outcome"]


def test_any_workflow_outcome_is_allowed_when_field_is_omitted() -> None:
    for outcome in ("answer", "clarify", "abort", "unknown"):
        decision = runner_evaluator(
            _case({"answer_contains": ["回答"]}),
            _output(answer="任意回答", outcome=outcome),
        )

        assert decision.passed is True
        assert decision.metadata["workflow_outcome_passed"] is True
