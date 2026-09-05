import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from evals.loader import load_cases
from evals.reporter import write_reports
from evals.runner import run_suite


DEFAULT_DATASET = Path(__file__).parent / "datasets" / "smoke.jsonl"
DEFAULT_REPORT_DIR = Path(__file__).parent / "reports"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Supersonic FC evaluations.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Explicitly allow calls to the real LangGraph Agent and its providers.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.live:
        print(
            "No evaluation was run. Pass --live to explicitly allow the real Agent "
            "or call evals.runner.run_suite with a mock agent_callable.",
            file=sys.stderr,
        )
        return 2

    # Deliberately lazy: importing this adapter may initialize production Agent/RAG
    # dependencies and is allowed only after the user explicitly passes --live.
    from evals.agent_adapter import run_agent_for_eval
    from evals.runner_evaluator import runner_evaluator

    cases = load_cases(args.dataset)
    results = run_suite(
        cases=cases,
        agent_callable=run_agent_for_eval,
        evaluator=runner_evaluator,
    )
    json_path, markdown_path = write_reports(results, args.output_dir)

    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    print("Evaluation V1 runner evaluator enabled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
