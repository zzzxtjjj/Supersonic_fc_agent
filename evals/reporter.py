import json
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from evals.metrics import calculate_metrics
from evals.schemas import EvalResult, EvaluationMetrics


def _format_rate(pass_rate: float | None) -> str:
    return "N/A" if pass_rate is None else f"{pass_rate:.2%}"


def render_markdown(
    results: Sequence[EvalResult],
    metrics: EvaluationMetrics,
    generated_at: str,
) -> str:
    lines = [
        "# Evaluation Summary",
        "",
        f"Generated: {generated_at}",
        "",
        f"- Total: {metrics.total_cases}",
        f"- Completed: {metrics.completed_cases}",
        f"- Passed: {metrics.passed_cases}",
        f"- Failed: {metrics.failed_cases}",
        f"- Errors: {metrics.error_cases}",
        f"- Not Evaluated: {metrics.not_evaluated_cases}",
        f"- Pass Rate: {_format_rate(metrics.pass_rate)}",
        f"- Average Latency: {metrics.average_latency_seconds:.6f}s",
        "",
        "## Cases",
    ]

    for result in results:
        lines.extend(
            [
                "",
                f"### {result.case_id}",
                "",
                f"- Category: {result.category}",
                f"- Question: {result.question}",
                f"- Result: {result.result}",
                f"- Error: {result.error or 'None'}",
                f"- Latency: {result.latency_seconds:.6f}s",
                "",
                "**Final Answer**",
                "",
                result.final_answer or "",
            ]
        )

    return "\n".join(lines) + "\n"


def write_reports(
    results: Sequence[EvalResult],
    output_dir: str | Path,
    timestamp: str | None = None,
) -> tuple[Path, Path]:
    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()
    filename_timestamp = timestamp or datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    metrics = calculate_metrics(results)

    json_path = report_dir / f"{filename_timestamp}.json"
    markdown_path = report_dir / f"{filename_timestamp}.md"

    json_payload = {
        "generated_at": generated_at,
        "summary": metrics.model_dump(mode="json"),
        "cases": [result.model_dump(mode="json") for result in results],
    }
    json_path.write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_markdown(results, metrics, generated_at),
        encoding="utf-8",
    )

    return json_path, markdown_path
