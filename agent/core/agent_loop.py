import json

from agent.llm.openrouter_client import call_llm
from agent.tools.executor import (
    execute_tool,
    TOOL_SCHEMAS,
)



def run_agent(user_input: str, max_steps: int = 5) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "你是超音速足球队 AI Agent。"
                "球衣号码、进球数、射手榜、比赛比分等精确事实，"
                "优先使用对应的结构化工具。"
                "球员技术特点、比赛风格、球队角色、战术、比赛分析、"
                "球队文化和历史等非结构化知识，使用 search_team_knowledge。"
                "如果问题需要多个工具，可以调用多个工具。"
                "最终回答必须严格依据工具返回结果，不得自行编造。"
                "26-27赛季除工具明确返回的队长事实外，缺少资料时只说明暂无相关数据；"
                "不得推测缺失原因、套用其他赛季信息，也不得推断正副队长或队长职责。"
                "调用 search_team_knowledge 时，season 必须与用户问题中的赛季一致；"
                "该工具返回 success=false 或 results=[] 后必须立即停止调用工具，只回答暂无相关数据，"
                "不得移除或更换 season 再次搜索。"
            )
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    step = 0

    while step < max_steps:
        result = call_llm(
            messages=messages,
            tools=TOOL_SCHEMAS
        )

        message = result["choices"][0]["message"]
        tool_calls = message.get("tool_calls", [])

        # 模型不再请求工具，说明准备给最终答案
        if not tool_calls:
            return message["content"]

        # 把 assistant 的 tool call 记录进对话历史
        messages.append(message)

        # 执行这一轮模型请求的所有工具
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]

            tool_result = execute_tool(
                tool_name=tool_name,
                arguments=arguments
            )
        
            # 把工具执行结果交回模型
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(
                        tool_result,
                        ensure_ascii=False
                    )
                }
            )

        step += 1

    return "Agent reached max steps."



if __name__ == "__main__":
    question = "张谢童甲25-26赛季进了几个球？他的技术特点是什么？"

    answer = run_agent(question)

    print("\n最终回答：")
    print(answer)
