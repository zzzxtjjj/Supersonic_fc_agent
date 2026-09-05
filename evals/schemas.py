from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


EvaluationStatus = Literal["passed", "failed", "error", "not_evaluated"]


class EvalExpected(BaseModel):
    """Human-authored expectations; the infrastructure never derives these."""

    model_config = ConfigDict(extra="forbid")

    answer_contains: list[str] = Field(default_factory=list)
    tool_names: list[str] = Field(default_factory=list)
    workflow_outcome: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    question: str = Field(min_length=1)
    expected: EvalExpected | None = None
    tags: list[str] = Field(default_factory=list)
    needs_manual_expected: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    final_answer: str
    trace: list[dict[str, Any]] = Field(default_factory=list)


class EvaluationDecision(BaseModel):
    """Result returned by a future user-supplied evaluator."""

    passed: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalResult(BaseModel):
    case_id: str
    category: str
    question: str
    final_answer: str | None = None
    latency_seconds: float = Field(ge=0)
    error: str | None = None
    result: EvaluationStatus
    metadata: dict[str, Any] = Field(default_factory=dict)
    trace: list[dict[str, Any]] = Field(default_factory=list)


class EvaluationMetrics(BaseModel):
    total_cases: int
    completed_cases: int
    passed_cases: int
    failed_cases: int
    error_cases: int
    not_evaluated_cases: int
    pass_rate: float | None
    average_latency_seconds: float
