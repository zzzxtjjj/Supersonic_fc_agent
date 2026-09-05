def extract_tool_names(
    messages: list[dict],
) -> list[str]:
    """
    从完整 messages 中提取 Agent 实际调用过的 Tool 名称。
    """

    tool_names = []

    for message in messages:
        if message.get("role") != "assistant":
            continue

        tool_calls = message.get("tool_calls", [])

        for tool_call in tool_calls:
            function_info = tool_call.get("function", {})
            tool_name = function_info.get("name")

            if isinstance(tool_name, str) and tool_name:
                tool_names.append(tool_name)
    
    return tool_names


def extract_final_answer(
    state: dict,
) -> str:
    """
    从最终 LangGraph State 中提取最终文本回答。
    """
    final_answer = state.get("final_answer")

    if isinstance(final_answer, str) and final_answer:
        return final_answer

    messages = state.get("messages", [])

    for message in reversed(messages):
        if message.get("role") != "assistant":
            continue

        content = message.get("content")

        if isinstance(content, str) and content:
            return content
    
    return ""


def extract_workflow_outcome(
    state: dict,
    final_answer: str,
) -> str:
    """
    推断本次 Agent workflow 的最终结果类型。
    """

    recovery_strategy = state.get("recovery_strategy")

    if recovery_strategy == "clarify":
        return "clarify"

    if recovery_strategy == "abort":
        return "abort"
   
    if final_answer:
        return "answer"

    return "unknown"


def extract_actual(
    state: dict,
) -> dict:
    """
    将 LangGraph final state 转换为 Evaluation V1 的 actual 格式。
    """

    messages = state.get("messages", [])

    tool_names = extract_tool_names(messages)

    final_answer = extract_final_answer(state)

    workflow_outcome = extract_workflow_outcome(
        state=state,
        final_answer=final_answer,
    )

    return {
        "final_answer": final_answer,
        "tool_names": tool_names,
        "workflow_outcome": workflow_outcome,
    }


if __name__ == "__main__":
    fake_state = {
        "messages": [
            {
                "role": "user",
                "content": "张谢童甲25-26赛季进了几个球？"
            },

            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {
                            "name": "get_player_goals",
                            "arguments": (
                                '{"name":"张谢童甲",'
                                '"season":"25-26"}'
                            )
                        }
                    }
                ]
            },

            {
                "role": "tool",
                "tool_call_id": "call_123",
                "content": (
                    '{"success":true,'
                    '"name":"张谢童甲",'
                    '"season":"25-26",'
                    '"goals":3}'
                )
            },

            {
                "role": "assistant",
                "content": "张谢童甲在25-26赛季进了3个球。"
            }
        ],

        "final_answer": None,
        "recovery_strategy": None,
    }

    actual = extract_actual(fake_state)

    print(actual)