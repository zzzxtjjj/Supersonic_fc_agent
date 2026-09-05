from agent.workflow.state import AgentState
from agent.llm.openrouter_client import call_llm
from agent.tools.executor import TOOL_SCHEMAS
from agent.tools.executor import execute_tool
import json


def llm_node(state: AgentState) -> dict:
    messages = state["messages"]

    result = call_llm(
        messages=messages,
        tools=TOOL_SCHEMAS
    )

    message = result["choices"][0]["message"]

    updated_messages = messages + [message]

    return {
        "messages": updated_messages
    }


def tool_node(state: AgentState) -> dict:
    messages = state["messages"]
    step = state["step"] + 1

    assistant_message = messages[-1]

    tool_calls = assistant_message.get("tool_calls", [])

    tool_messages = []

    for tool_call in tool_calls:
        tool_name = tool_call["function"]["name"]

        arguments = tool_call["function"]["arguments"]

        tool_result = execute_tool(
            tool_name=tool_name,
            arguments=arguments
        )

        tool_message = {
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": json.dumps(tool_result, ensure_ascii=False)
        }

        tool_messages.append(tool_message)

    updated_messages = messages + tool_messages

    return {
        "messages": updated_messages,
        "step": step
    }


def verify_tool_results_node(state: AgentState) -> dict:
    messages = state["messages"]

    recent_tool_messages = []

    for message in reversed(messages):
        if message.get("role") != "tool":
            break

        recent_tool_messages.append(message)

    if not recent_tool_messages:
        return {
            "verification_status": "failed",
            "verification_reason": "No tool result found."
        }

    for tool_message in recent_tool_messages:
        try:
            tool_result = json.loads(tool_message["content"])
        except (json.JSONDecodeError, KeyError, TypeError):
            return {
                "verification_status": "failed",
                "verification_reason": "Tool result is not valid JSON."
            }

        if not isinstance(tool_result, dict):
            return {
                "verification_status": "failed",
                "verification_reason": "Tool result is not a JSON object."
            }

        if tool_result.get("success") is not True:
            return {
                "verification_status": "failed",
                "verification_reason": tool_result.get("error", "Tool execution failed.")
            }

    return {
        "verification_status": "passed",
        "verification_reason": None,
        "retry_count": 0
    }


def recovery_node(state: AgentState) -> dict:
    messages = state["messages"]
    reason = state["verification_reason"]
    retry_count = state["retry_count"] + 1

    recovery_message = {
        "role": "system",
        "content": (
            f"上一次工具执行失败，原因：{reason}。"
            f"当前正在进行第 {retry_count} 次重试。"
            "请根据失败原因重新判断下一步。"
            "如果可以修正工具参数，请修正后重新调用。"
            "如果是临时性工具错误，可以重新尝试。"
            "不得通过猜测或编造事实绕过工具失败。"
        )
    }

    updated_messages = messages + [recovery_message]

    return {
        "messages": updated_messages,

        "retry_count": retry_count,

        "verification_status": "pending",
        "verification_reason": None,

        "recovery_strategy": "retry"
    }


def grounding_recovery_node(state: AgentState) -> dict:
    messages = state["messages"]
    grounding_retry_count = state["grounding_retry_count"] + 1

    grounding_message = {
        "role": "system",
        "content": (
            "你刚才在没有经过工具或知识库验证的情况下直接回答了球队事实，"
            "这是不允许的。请重新判断用户问题并调用合适的结构化工具或球队"
            "知识检索工具。不得猜测。如果无法确认，请明确说明无法确认。"
        )
    }

    return {
        "messages": messages + [grounding_message],
        "grounding_retry_count": grounding_retry_count,
    }


def clarify_node(state: AgentState) -> dict:
    messages = state["messages"]

    reason = state["verification_reason"]

    if reason == "player_not_found":
        answer = (
            "没有找到该球员。"
            "请确认球员姓名是否正确，或告诉我他的队内昵称。"
        )
    else:
        answer = (
            "当前信息不足，请补充或确认相关信息。"
        )

    clarify_message = {
        "role": "assistant",
        "content": answer
    }

    updated_messages = messages + [clarify_message]

    return {
        "messages": updated_messages,
        "final_answer": answer,
        "recovery_strategy": "clarify"
    }


def abort_node(state: AgentState) -> dict:
    messages = state["messages"]

    answer = (
        "当前任务无法可靠完成，请稍后重试或补充更多信息。"
    )

    abort_message = {
        "role": "assistant",
        "content": answer
    }

    updated_messages = messages + [abort_message]

    return {
        "messages": updated_messages,
        "final_answer": answer,
        "recovery_strategy": "abort"
    }


def collect_recent_tool_records(state: AgentState) -> list[dict]:
    messages = state["messages"]

    recent_tool_messages = []

    index = len(messages) - 1

    # 从尾部收集最近连续的 tool messages
    while index >= 0 and messages[index].get("role") == "tool":
        recent_tool_messages.append(messages[index])
        index -= 1

    if not recent_tool_messages:
        return []

    # tool messages 前面应该是发起调用的 assistant message
    if index < 0:
        return []

    assistant_message = messages[index]

    if assistant_message.get("role") != "assistant":
        return []

    tool_calls = assistant_message.get("tool_calls", [])

    # {
    #   "call_1": {...tool_call...},
    #   "call_2": {...tool_call...}
    # }
    tool_call_map = {
        tool_call["id"]: tool_call
        for tool_call in tool_calls
        if isinstance(tool_call, dict) and tool_call.get("id")
    }

    records = []

    # 恢复原顺序
    for tool_message in reversed(recent_tool_messages):

        tool_call_id = tool_message.get("tool_call_id")

        tool_call = tool_call_map.get(tool_call_id)

        if tool_call is None:
            continue

        function = tool_call.get("function")

        if not isinstance(function, dict):
            continue

        tool_name = function.get("name")

        if not isinstance(tool_name, str) or not tool_name:
            continue

        raw_arguments = function.get("arguments")

        try:
            arguments = json.loads(raw_arguments)
        except (json.JSONDecodeError, TypeError):
            arguments = {}

        if not isinstance(arguments, dict):
            arguments = {}

        try:
            result = json.loads(tool_message.get("content"))
        except (json.JSONDecodeError, TypeError):
            result = {}

        if not isinstance(result, dict):
            result = {}

        record = {
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
        }

        records.append(record)

    return records


def verify_evidence_node(state: AgentState) -> dict:
    records = collect_recent_tool_records(state)

    if not records:
        return {
            "evidence_status": "insufficient",
            "evidence_reason": "No evidence record found."
        }

    for record in records:
        tool_name = record["tool_name"]
        arguments = record["arguments"]
        result = record["result"]

        if tool_name == "get_player_goals":
            requested_name = arguments.get("name")
            returned_name = result.get("name")

            requested_season = arguments.get("season")
            returned_season = result.get("season")

            if requested_name is None or returned_name is None:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Player identity evidence is missing."
                }

            if requested_name != returned_name:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Player identity does not match."
                }

            if requested_season is None or returned_season is None:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Season evidence is missing."
                }

            if requested_season != returned_season:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Season does not match."
                }

        elif tool_name == "get_player_number":
            requested_name = arguments.get("name")
            returned_name = result.get("name")

            if requested_name is None or returned_name is None:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Player identity evidence is missing."
                }

            if requested_name != returned_name:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Player identity does not match."
                }

        elif tool_name == "get_player_profile":
            requested_name = arguments.get("name")
            returned_name = result.get("name")

            if requested_name is None or returned_name is None:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Player identity evidence is missing."
                }

            if requested_name != returned_name:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Player identity does not match."
                }

        elif tool_name == "search_team_knowledge":
            requested_player = arguments.get("player")
            knowledge_type = arguments.get("knowledge_type")

            filters = result.get("filters", {})
            rag_results = result.get("results", [])

            # 1. RAG 没有检索到任何证据
            if not rag_results:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "RAG returned no evidence."
                }

            # 2. 如果明确是在查询球员知识，
            #    第一版要求必须带明确 player filter
            if knowledge_type == "player" and requested_player is None:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": (
                        "Player knowledge search requires an explicit player filter."
                    )
                }

            # 3. 如果请求了具体球员，确认检索过滤条件没有跑偏
            if requested_player is not None:
                filtered_player = filters.get("player")

                if filtered_player != requested_player:
                    return {
                        "evidence_status": "insufficient",
                        "evidence_reason": "RAG player filter does not match the requested player."
                    }

                # 4. 再检查真正返回的文本里至少有一条明确提到这个球员
                player_supported = False

                for item in rag_results:
                    title = item.get("title", "")
                    text = item.get("text", "")

                    if requested_player in title or requested_player in text:
                        player_supported = True
                        break

                if not player_supported:
                    return {
                        "evidence_status": "insufficient",
                        "evidence_reason": (
                            "Retrieved evidence does not support the requested player identity."
                        )
                    }

        elif tool_name == "get_match_result":
            requested_season = arguments.get("season")
            returned_season = result.get("season")

            requested_opponent = arguments.get("opponent")
            returned_opponent = result.get("opponent")

            if requested_season is None or returned_season is None:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Match season evidence is missing."
                }

            if requested_season != returned_season:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Match season does not match."
                }

            if requested_opponent is None or returned_opponent is None:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Match opponent evidence is missing."
                }

            if requested_opponent != returned_opponent:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Match opponent does not match."
                }

            if result.get("score") is None:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Match score evidence is missing."
                }

        elif tool_name == "get_scorer_ranking":
            requested_season = arguments.get("season")
            returned_season = result.get("season")

            ranking = result.get("ranking")

            if requested_season is None or returned_season is None:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Scorer ranking season evidence is missing."
                }

            if requested_season != returned_season:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Scorer ranking season does not match."
                }

            if not isinstance(ranking, list) or not ranking:
                return {
                    "evidence_status": "insufficient",
                    "evidence_reason": "Scorer ranking evidence is missing."
                }

        else:
            return {
                "evidence_status": "insufficient",
                "evidence_reason": f"Evidence verification is not implemented for tool: {tool_name}"
            }

    return {
        "evidence_status": "supported",
        "evidence_reason": None
    }


def evidence_insufficient_node(state: AgentState) -> dict:
    messages = state["messages"]
    reason = state["evidence_reason"]

    answer = (
        "当前获得的证据不足以可靠回答这个问题。"
        "请确认球员姓名、赛季或提供更具体的信息。"
    )

    assistant_message = {
        "role": "assistant",
        "content": answer
    }

    updated_messages = messages + [assistant_message]

    return {
        "messages": updated_messages,
        "final_answer": answer,
        "recovery_strategy": "clarify"
    }
