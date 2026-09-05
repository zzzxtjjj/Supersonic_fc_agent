import re

from agent.workflow.state import AgentState


TEAM_FACT_KEYWORDS = (
    "超音速",
    "球队",
    "球员",
    "进球",
    "几个球",
    "球衣",
    "号码",
    "射手榜",
    "比分",
    "比赛",
    "排名",
    "赛季",
    "数据",
    "技术特点",
    "技术风格",
    "角色",
    "战术",
    "文化",
    "历史",
    "故事",
    "助攻",
    "出场",
    "阵容",
    "队长",
    "位置",
    "外号",
    "昵称",
)

CASUAL_MESSAGES = {
    "你好",
    "您好",
    "嗨",
    "hello",
    "hi",
    "你是谁",
    "你是什么",
    "谢谢",
}

AGENT_META_MESSAGES = {
    "你是谁",
    "你是什么",
    "介绍一下你自己",
    "你能做什么",
    "你会什么",
    "你的功能是什么",
    "你的功能",
    "你的能力是什么",
    "你的能力",
}

CASUAL_PREFIX_PATTERN = re.compile(
    r"^(?:(?:你好|您好|嗨|hello|hi|请问)[\s，,。！？!?]*)+",
    re.IGNORECASE,
)


def _normalize_query(content: str) -> str:
    return content.strip().lower().rstrip("。！？!? ")


def is_agent_meta_query(content: str) -> bool:
    normalized = _normalize_query(content)

    if normalized in CASUAL_MESSAGES:
        return True

    without_prefix = CASUAL_PREFIX_PATTERN.sub("", normalized)
    without_prefix = without_prefix.strip().rstrip("。！？!? ")

    return without_prefix in AGENT_META_MESSAGES


def requires_team_grounding(state: AgentState) -> bool:
    user_message = next(
        (
            message
            for message in reversed(state["messages"])
            if message.get("role") == "user"
        ),
        None,
    )

    if user_message is None:
        return False

    content = user_message.get("content")

    if not isinstance(content, str):
        return False

    if is_agent_meta_query(content):
        return False

    normalized = _normalize_query(content)

    return (
        any(keyword in content for keyword in TEAM_FACT_KEYWORDS)
        or re.search(r"\d{2}[-–]\d{2}", content) is not None
        or normalized.endswith("是谁")
    )


def route_after_llm(state: AgentState) -> str:
    step = state["step"]
    max_steps = state["max_steps"]

    messages = state["messages"]
    assistant_message = messages[-1]

    tool_calls = assistant_message.get("tool_calls", [])

    if tool_calls:
        if step >= max_steps:
            return "max_steps"

        return "tools"

    if state["evidence_status"] == "supported":
        return "end"

    if requires_team_grounding(state):
        if state["grounding_retry_count"] >= state["max_grounding_retries"]:
            return "max_steps"

        return "ungrounded"

    return "end"


def route_after_verifier(state: AgentState) -> str:
    verification_status = state["verification_status"]

    if verification_status == "passed":
        return "passed"

    return choose_recovery_strategy(state)


def choose_recovery_strategy(state: AgentState) -> str:
    reason = state["verification_reason"]

    retry_count = state["retry_count"]
    max_retries = state["max_retries"]

    if reason == "player_not_found":
        return "clarify"

    if reason is None:
        return "abort"

    if retry_count >= max_retries:
        return "abort"

    return "retry"


def route_after_evidence(state: AgentState) -> str:
    evidence_status = state["evidence_status"]

    if evidence_status == "supported":
        return "supported"

    return "insufficient"
