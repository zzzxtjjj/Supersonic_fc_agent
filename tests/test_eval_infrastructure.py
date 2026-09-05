import builtins
import json
import socket

from evals.loader import load_cases
from evals.metrics import calculate_metrics
from evals.reporter import write_reports
from evals.run_eval import main
from evals.runner import run_suite
from evals.schemas import EvalCase, EvalResult


def _case(case_id: str, question: str | None = None) -> EvalCase:
    return EvalCase(
        id=case_id,
        category="test",
        question=question or f"question for {case_id}",
        tags=["unit"],
    )


def test_jsonl_loads_valid_cases(tmp_path) -> None:
    dataset = tmp_path / "cases.jsonl"
    dataset.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "case_1",
                        "category": "structured_fact",
                        "question": "question one",
                        "expected": {
                            "answer_contains": ["manual value"],
                            "tool_names": ["manual_tool"],
                        },
                        "tags": ["smoke"],
                    }
                ),
                json.dumps(
                    {
                        "id": "case_2",
                        "category": "rag_knowledge",
                        "question": "question two",
                        "needs_manual_expected": True,
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    cases = load_cases(dataset)

    assert [case.id for case in cases] == ["case_1", "case_2"]
    assert cases[0].expected.answer_contains == ["manual value"]
    assert cases[1].needs_manual_expected is True


def test_example_datasets_load_without_deriving_expectations() -> None:
    smoke_cases = load_cases("evals/datasets/smoke.jsonl")
    regression_cases = load_cases("evals/datasets/regression.jsonl")

    assert len(smoke_cases) == 2
    assert len(regression_cases) == 2
    assert all(case.expected is not None for case in smoke_cases + regression_cases)
    assert all(case.needs_manual_expected for case in regression_cases)


def test_runner_executes_multiple_cases_with_injected_evaluator() -> None:
    calls: list[str] = []

    def fake_agent(question: str) -> str:
        calls.append(question)
        return f"mock answer: {question}"

    def fake_evaluator(case: EvalCase, agent_output) -> bool:
        return case.id == "pass_case"

    cases = [_case("pass_case"), _case("fail_case")]
    results = run_suite(cases, fake_agent, evaluator=fake_evaluator)

    assert calls == [case.question for case in cases]
    assert [result.result for result in results] == ["passed", "failed"]
    assert all(result.final_answer.startswith("mock answer:") for result in results)


def test_agent_exception_does_not_stop_suite() -> None:
    def fake_agent(question: str) -> str:
        if question == "explode":
            raise RuntimeError("controlled failure")
        return "mock answer"

    cases = [
        _case("before", "ok before"),
        _case("broken", "explode"),
        _case("after", "ok after"),
    ]
    results = run_suite(cases, fake_agent)

    assert [result.result for result in results] == [
        "not_evaluated",
        "error",
        "not_evaluated",
    ]
    assert results[1].final_answer is None
    assert results[1].error == "RuntimeError: controlled failure"
    assert results[2].final_answer == "mock answer"


def test_metrics_are_mechanical_and_correct() -> None:
    results = [
        EvalResult(
            case_id="passed",
            category="test",
            question="q1",
            final_answer="a1",
            latency_seconds=1.0,
            result="passed",
        ),
        EvalResult(
            case_id="failed",
            category="test",
            question="q2",
            final_answer="a2",
            latency_seconds=3.0,
            result="failed",
        ),
        EvalResult(
            case_id="error",
            category="test",
            question="q3",
            latency_seconds=2.0,
            error="controlled",
            result="error",
        ),
        EvalResult(
            case_id="not_evaluated",
            category="test",
            question="q4",
            final_answer="a4",
            latency_seconds=5.0,
            result="not_evaluated",
        ),
    ]

    metrics = calculate_metrics(results)

    assert metrics.total_cases == 4
    assert metrics.completed_cases == 3
    assert metrics.passed_cases == 1
    assert metrics.failed_cases == 1
    assert metrics.error_cases == 1
    assert metrics.not_evaluated_cases == 1
    assert metrics.pass_rate == 0.5
    assert metrics.average_latency_seconds == 3.0


def test_json_and_markdown_reports_are_generated_without_private_trace(
    tmp_path,
) -> None:
    def fake_agent(question: str) -> dict:
        return {
            "final_answer": "mock answer",
            "trace": [
                {
                    "tool_name": "mock_tool",
                    "status": "ok",
                    "reasoning": "must not be reported",
                    "nested": {
                        "reasoning_details": "must not be reported",
                        "api_key": "must not be reported",
                    },
                }
            ],
            "reasoning": "ignored top-level field",
        }

    results = run_suite([_case("report_case")], fake_agent)
    json_path, markdown_path = write_reports(
        results,
        tmp_path,
        timestamp="20260904T000000Z",
    )

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    combined_output = json_path.read_text(encoding="utf-8") + markdown

    assert json_path.name == "20260904T000000Z.json"
    assert markdown_path.name == "20260904T000000Z.md"
    assert payload["summary"]["total_cases"] == 1
    assert payload["summary"]["not_evaluated_cases"] == 1
    assert payload["cases"][0]["trace"][0]["tool_name"] == "mock_tool"
    assert "# Evaluation Summary" in markdown
    assert "### report_case" in markdown
    assert "mock answer" in markdown
    assert "must not be reported" not in combined_output
    assert "reasoning_details" not in combined_output
    assert "api_key" not in combined_output


def test_fake_suite_uses_no_network_llm_rag_or_real_tools(monkeypatch) -> None:
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        blocked_prefixes = ("agent.llm", "agent.rag", "agent.tools")
        if name.startswith(blocked_prefixes):
            raise AssertionError(f"production dependency imported: {name}")
        return real_import(name, globals, locals, fromlist, level)

    def blocked_connect(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(socket.socket, "connect", blocked_connect)

    results = run_suite([_case("offline")], lambda question: "offline mock")

    assert results[0].result == "not_evaluated"
    assert results[0].final_answer == "offline mock"


def test_cli_requires_explicit_live_flag(capsys) -> None:
    exit_code = main(["--dataset", "evals/datasets/smoke.jsonl"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--live" in captured.err
