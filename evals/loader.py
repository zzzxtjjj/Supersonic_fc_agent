import json
from pathlib import Path

from pydantic import ValidationError

from evals.schemas import EvalCase


class EvalDatasetError(ValueError):
    """Raised when an evaluation JSONL file is malformed or inconsistent."""


def load_cases(dataset_path: str | Path) -> list[EvalCase]:
    path = Path(dataset_path)
    cases: list[EvalCase] = []
    seen_ids: set[str] = set()

    with path.open("r", encoding="utf-8") as dataset_file:
        for line_number, raw_line in enumerate(dataset_file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                payload = json.loads(line)
                case = EvalCase.model_validate(payload)
            except (json.JSONDecodeError, ValidationError) as exc:
                raise EvalDatasetError(
                    f"Invalid evaluation case at {path}:{line_number}: {exc}"
                ) from exc

            if case.id in seen_ids:
                raise EvalDatasetError(
                    f"Duplicate evaluation case id at {path}:{line_number}: {case.id}"
                )

            seen_ids.add(case.id)
            cases.append(case)

    return cases
