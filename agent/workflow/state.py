from typing import TypedDict


class AgentState(TypedDict):
    messages: list[dict]

    step: int
    max_steps: int

    retry_count: int
    max_retries: int

    grounding_retry_count: int
    max_grounding_retries: int

    final_answer: str | None

    verification_status: str
    verification_reason: str | None

    recovery_strategy: str | None

    evidence_status: str
    evidence_reason: str | None
