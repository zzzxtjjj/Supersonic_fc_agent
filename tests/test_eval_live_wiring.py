import json
import socket

from evals import agent_adapter
from evals.run_eval import main
from evals.runner import run_suite
from evals.runner_evaluator import runner_evaluator
from evals.schemas import EvalCase, EvalExpected


def _case(
    case_id: str,
    *,
    answer_contains: list[str],
    tool_names: list[str],
    workflow_outcome: str,
) -> EvalCase:
    return EvalCase(
        id=case_id,
        category="integration",
        question=case_id,
        expected=EvalExpected(
            answer_contains=answer_contains,
            tool_names=tool_names,
            workflow_outcome=workflow_outcome,
        ),
    )


def test_runner_evaluator_handles_v1_outcomes_without_external_calls(
    monkeypatch,
) -> None:
    def blocked_connect(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)

    cases = [
        _case(
            "structured_pass",
            answer_contains=["3"],
            tool_names=["get_player_goals"],
            workflow_outcome="answer",
        ),
        _case(
            "tool_error_fails",
            answer_contains=["3"],
            tool_names=["get_player_goals"],
            workflow_outcome="answer",
        ),
        _case(
            "clarify_pass",
            answer_contains=["没有找到"],
            tool_names=["get_player_goals"],
            workflow_outcome="clarify",
        ),
        _case(
            "greeting_pass",
            answer_contains=["超音速"],
            tool_names=[],
            workflow_outcome="answer",
        ),
    ]
    outputs = {
        "structured_pass": {
            "final_answer": "张谢童甲25-26赛季进了3球。",
            "trace": [
                {"event": "tool_call", "tool_name": "get_player_goals"},
                {
                    "event": "tool_result",
                    "tool_name": "get_player_goals",
                    "success": True,
                },
                {"event": "execution_verification", "status": "passed"},
                {"event": "evidence_verification", "status": "supported"},
                {"event": "workflow_end", "outcome": "answer"},
            ],
        },
        "tool_error_fails": {
            "final_answer": "没有找到该球员。",
            "trace": [
                {"event": "tool_call", "tool_name": "get_player_goals"},
                {
                    "event": "tool_result",
                    "tool_name": "get_player_goals",
                    "success": False,
                },
                {"event": "execution_verification", "status": "failed"},
                {"event": "workflow_end", "outcome": "clarify"},
            ],
        },
        "clarify_pass": {
            "final_answer": "没有找到该球员。",
            "trace": [
                {"event": "tool_call", "tool_name": "get_player_goals"},
                {
                    "event": "tool_result",
                    "tool_name": "get_player_goals",
                    "success": False,
                },
                {"event": "execution_verification", "status": "failed"},
                {"event": "workflow_end", "outcome": "clarify"},
            ],
        },
        "greeting_pass": {
            "final_answer": "你好，我是超音速足球队 AI Agent。",
            "trace": [{"event": "workflow_end", "outcome": "answer"}],
        },
    }

    evaluator_calls: list[str] = []

    def recording_evaluator(case, agent_output):
        evaluator_calls.append(case.id)
        return runner_evaluator(case, agent_output)

    results = run_suite(
        cases=cases,
        agent_callable=lambda question: outputs[question],
        evaluator=recording_evaluator,
    )

    assert evaluator_calls == [case.id for case in cases]
    assert [result.result for result in results] == [
        "passed",
        "failed",
        "passed",
        "passed",
    ]


def test_live_cli_uses_structured_adapter_and_runner_evaluator(
    monkeypatch,
    tmp_path,
) -> None:
    dataset = tmp_path / "live.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "greeting_live",
                "category": "casual",
                "question": "你好，你是谁？",
                "expected": {
                    "answer_contains": ["超音速"],
                    "tool_names": [],
                    "workflow_outcome": "answer",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    adapter_calls: list[str] = []

    def fake_eval_agent(question: str) -> dict:
        adapter_calls.append(question)
        return {
            "final_answer": "你好，我是超音速足球队 AI Agent。",
            "trace": [{"event": "workflow_end", "outcome": "answer"}],
        }

    monkeypatch.setattr(agent_adapter, "run_agent_for_eval", fake_eval_agent)

    output_dir = tmp_path / "reports"
    exit_code = main(
        [
            "--live",
            "--dataset",
            str(dataset),
            "--output-dir",
            str(output_dir),
        ]
    )

    reports = sorted(output_dir.glob("*.json"))
    assert exit_code == 0
    assert adapter_calls == ["你好，你是谁？"]
    assert len(reports) == 1
    report = json.loads(reports[0].read_text(encoding="utf-8"))
    assert report["cases"][0]["result"] == "passed"
    assert report["cases"][0]["metadata"]["evaluator"]["passed"] is True
