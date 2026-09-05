from collections.abc import Sequence

from evals.schemas import EvalResult, EvaluationMetrics


def calculate_metrics(results: Sequence[EvalResult]) -> EvaluationMetrics:
    total_cases = len(results)
    passed_cases = sum(result.result == "passed" for result in results)
    failed_cases = sum(result.result == "failed" for result in results)
    error_cases = sum(result.result == "error" for result in results)
    not_evaluated_cases = sum(
        result.result == "not_evaluated" for result in results
    )
    completed_results = [result for result in results if result.result != "error"]
    completed_cases = len(completed_results)

    evaluated_cases = passed_cases + failed_cases
    pass_rate = passed_cases / evaluated_cases if evaluated_cases else None
    average_latency = (
        sum(result.latency_seconds for result in completed_results) / completed_cases
        if completed_cases
        else 0.0
    )

    return EvaluationMetrics(
        total_cases=total_cases,
        completed_cases=completed_cases,
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        error_cases=error_cases,
        not_evaluated_cases=not_evaluated_cases,
        pass_rate=pass_rate,
        average_latency_seconds=average_latency,
    )
