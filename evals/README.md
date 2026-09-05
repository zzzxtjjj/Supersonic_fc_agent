# Agent Evaluation Infrastructure

This directory provides evaluation plumbing, not evaluation judgment.

## Pipeline

```text
Dataset → Runner → Agent → Evaluator → Metrics → Report
```

- **Dataset:** human-authored JSONL cases and expectations.
- **Runner:** invokes an injected `agent_callable` once per case and isolates errors.
- **Agent:** may return a string or `{ "final_answer": "...", "trace": [...] }`.
- **Evaluator:** optional, injected code that returns pass/fail. No evaluator is
  implemented here.
- **Metrics:** mechanical counts, pass rate, and average latency only.
- **Report:** timestamped JSON and Markdown files under `evals/reports/`.

## Infrastructure vs. logic

This package owns file loading, schema validation, batch execution, exception
isolation, mechanical aggregation, and report formatting. It does not decide
whether an answer is semantically correct.

Evidence correctness, groundedness, semantic judging, final-answer verification,
and scoring policy are TODOs that will be implemented by the project owner.
Expected values in datasets are always written by a human; the framework never
generates them.

## Case format

```json
{
  "id": "player_goals_001",
  "category": "structured_fact",
  "question": "张谢童甲25-26赛季进了几个球？",
  "expected": {
    "answer_contains": ["3"],
    "tool_names": ["get_player_goals"]
  },
  "tags": ["player", "structured", "25-26"],
  "needs_manual_expected": false,
  "metadata": {}
}
```

`expected` is storage for human-authored expectations. The infrastructure does
not evaluate it automatically. Use `needs_manual_expected: true` whenever the
semantic answer criteria still require manual work.

## Python API

```python
from evals.loader import load_cases
from evals.runner import run_suite


def fake_agent(question: str) -> str:
    return "mock answer"


cases = load_cases("evals/datasets/smoke.jsonl")
results = run_suite(cases, agent_callable=fake_agent, evaluator=None)
```

The optional evaluator signature is:

```python
evaluator(case, agent_output) -> bool | EvaluationDecision | None
```

With no evaluator, each completed case is `not_evaluated`. A mapping Agent
response may include an optional trace. Before reporting, the runner removes
private keys such as `reasoning`, `reasoning_details`, and API credentials.

## CLI safety

The CLI does not call the real Agent by default:

```powershell
python -m evals.run_eval --dataset evals/datasets/smoke.jsonl
```

It exits with an explanation. A real execution requires explicit authorization:

```powershell
python -m evals.run_eval --dataset evals/datasets/smoke.jsonl --live
```

`--live` lazily imports the existing LangGraph runner. It does not add evaluation
logic, and without an injected evaluator the generated results remain
`not_evaluated`.

## Structured Agent trace adapter

`evals.agent_adapter.run_agent_for_eval(question)` runs the existing graph and
returns `{ "final_answer": str, "trace": list[dict] }`. It observes graph node
updates without changing Agent routing or verification behavior. Trace events
are limited to tool calls/results, execution and evidence verification,
grounding recovery, and one final workflow outcome. Tool arguments, prompts,
model reasoning, and credentials are never copied into the trace.

## Metrics definitions

- `completed_cases`: Agent calls that returned without an error.
- `pass_rate`: passed divided by passed plus failed; `null` when no evaluator ran.
- `average_latency_seconds`: mean latency of completed Agent calls.
- Errors and unevaluated cases are counted separately.
