from agent.workflow.graph import graph


SYSTEM_PROMPT = (
    "你是超音速足球队 AI Assistant。"
    "球衣号码、进球数、射手榜、比赛比分等精确事实优先使用结构化工具。"
    "球员技术特点、球队角色、战术、球队文化和历史使用球队知识检索工具。"
    "如果用户询问某球员为什么不在某赛季最终射手榜，"
    "必须同时调用 get_scorer_ranking 核对最终榜单，并调用 "
    "search_team_knowledge 核对该球员的转会或排除原因；"
    "不得仅依据历史进球数判断他是否进入最终榜单。"

    "不得自行推断两个不同名称指向同一名球员。"
    "只有当工具或知识库明确给出姓名、昵称、别名之间的对应关系时，"
    "才能认定两个名称属于同一人。"
    "如果查询的球员不存在，且没有明确别名证据，必须说明未找到该球员，"
    "并请用户确认姓名或昵称，不得根据相似度、进球数、排名或检索顺序猜测身份。"

    "最终回答必须依据工具返回结果，不得自行编造。"
    "回答应简洁直接，逐项核对人名、进球数、比分、赛季和事件顺序；"
    "工具或知识库未明确给出的球员贡献、统计和评价不得补充。"
    "只回答用户问题直接需要的内容，不主动扩写无关的球员表现、排名或心理影响。"
    "除非用户明确要求详细展开，默认用不超过120个中文字的纯文本或简短要点回答，"
    "不使用表格、多级标题或修辞性扩写。"
    "证据中的‘联赛第四’不得改写为‘队史第四’。"
    "除非证据明确如此表述，不得使用‘史诗级’、‘奇迹’、‘彻底决定’等夸张结论。"
)


NO_FINAL_ANSWER = "Agent 未生成可用的最终回答。"


def _extract_final_answer(state: dict) -> str:
    final_answer = state.get("final_answer")

    if isinstance(final_answer, str) and final_answer.strip():
        return final_answer

    for message in reversed(state.get("messages", [])):
        content = message.get("content")

        if (
            message.get("role") == "assistant"
            and isinstance(content, str)
            and content.strip()
        ):
            return content

    return NO_FINAL_ANSWER


def _sanitize_trace(value):
    if isinstance(value, dict):
        return {
            key: _sanitize_trace(item)
            for key, item in value.items()
            if key not in {"reasoning", "reasoning_details"}
        }

    if isinstance(value, list):
        return [_sanitize_trace(item) for item in value]

    return value


def run_graph_agent(user_input: str, max_steps: int = 5) -> str:
    initial_state = {
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        "step": 0,
        "max_steps": max_steps,
        "retry_count": 0,
        "max_retries": 2,
        "grounding_retry_count": 0,
        "max_grounding_retries": 2,
        "final_answer": None,
        "verification_status": "pending",
        "verification_reason": None,
        "recovery_strategy": None,
        "evidence_status": "pending",
        "evidence_reason": None,
    }

    result = graph.invoke(initial_state)

    return _extract_final_answer(result)


# stream方便遍历事件流
def trace_graph_agent(user_input: str, max_steps: int = 5) -> str:
    initial_state = {
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_input
            }
        ],

        "step": 0,
        "max_steps": max_steps,

        "retry_count": 0,
        "max_retries": 2,

        "grounding_retry_count": 0,
        "max_grounding_retries": 2,

        "verification_status": "pending",
        "verification_reason": None,

        "evidence_status": "pending",
        "evidence_reason": None,

        "recovery_strategy": None,
        "final_answer": None,
    }

    final_state = None

    for state in graph.stream(
        initial_state,
        stream_mode="values"
    ):
        print(_sanitize_trace(state))
        final_state = state

    if final_state is None:
        return NO_FINAL_ANSWER

    return _extract_final_answer(final_state)


if __name__ == "__main__":
    answer = trace_graph_agent(
        "你好，你是谁？"
    )

    print("\n最终回答：")
    print(answer)
