import sys
from types import ModuleType
from unittest.mock import Mock
from unittest.mock import patch


def _unexpected_external_call(*args, **kwargs):
    raise AssertionError("External LLM/tool code must be monkeypatched in this test.")


# nodes.py imports the production LLM client and tool executor at module load time.
# Isolate those imports so test collection never loads RAG models or real tools.
_llm_stub = ModuleType("agent.llm.openrouter_client")
_llm_stub.call_llm = _unexpected_external_call
_executor_stub = ModuleType("agent.tools.executor")
_executor_stub.TOOL_SCHEMAS = []
_executor_stub.execute_tool = _unexpected_external_call

with patch.dict(
    sys.modules,
    {
        "agent.llm.openrouter_client": _llm_stub,
        "agent.tools.executor": _executor_stub,
    },
):
    from agent.workflow import nodes
    from agent.workflow.graph import graph


def _initial_state(*, max_retries: int = 2) -> dict:
    return {
        "messages": [
            {"role": "system", "content": "test system prompt"},
            {"role": "user", "content": "test"},
        ],
        "step": 0,
        "max_steps": 5,
        "retry_count": 0,
        "max_retries": max_retries,
        "grounding_retry_count": 0,
        "max_grounding_retries": 2,
        "final_answer": None,
        "verification_status": "pending",
        "verification_reason": None,
        "evidence_status": "pending",
        "evidence_reason": None,
        "recovery_strategy": None,
    }


def _tool_call_response(tool_call_id: str) -> dict:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": "get_player_goals",
                                "arguments": (
                                    '{"name":"张谢童甲","season":"25-26"}'
                                ),
                            },
                        }
                    ],
                }
            }
        ]
    }


def _final_response(content: str = "任务最终成功。") -> dict:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                }
            }
        ]
    }


def _recovery_messages(result: dict) -> list[dict]:
    return [
        message
        for message in result["messages"]
        if message.get("role") == "system"
        and "工具执行失败" in message.get("content", "")
    ]


def test_retry_once_then_success(monkeypatch) -> None:
    mock_call_llm = Mock(
        side_effect=[
            _tool_call_response("call_test_1"),
            _tool_call_response("call_test_2"),
            _final_response(),
        ]
    )
    mock_execute_tool = Mock(
        side_effect=[
            {"success": False, "error": "tool_timeout"},
            {
                "success": True,
                "name": "张谢童甲",
                "season": "25-26",
                "goals": 3,
            },
        ]
    )
    monkeypatch.setattr(nodes, "call_llm", mock_call_llm)
    monkeypatch.setattr(nodes, "execute_tool", mock_execute_tool)

    result = graph.invoke(_initial_state(), config={"recursion_limit": 20})

    assert mock_execute_tool.call_count == 2
    assert mock_call_llm.call_count == 3
    assert result["messages"][-1]["content"] == "任务最终成功。"
    assert result["retry_count"] == 0
    assert result["recovery_strategy"] == "retry"

    recovery_messages = _recovery_messages(result)
    assert len(recovery_messages) == 1
    recovery_content = recovery_messages[0]["content"]
    assert "第 1 次重试" in recovery_content
    assert "第 2 次重试" not in recovery_content
    assert "tool_timeout" in recovery_content

    assert [call.kwargs for call in mock_execute_tool.call_args_list] == [
        {
            "tool_name": "get_player_goals",
            "arguments": '{"name":"张谢童甲","season":"25-26"}',
        },
        {
            "tool_name": "get_player_goals",
            "arguments": '{"name":"张谢童甲","season":"25-26"}',
        },
    ]


def test_max_retries_aborts_without_infinite_loop(monkeypatch) -> None:
    mock_call_llm = Mock(
        side_effect=[
            _tool_call_response("call_test_1"),
            _tool_call_response("call_test_2"),
            _tool_call_response("call_test_3"),
        ]
    )
    mock_execute_tool = Mock(
        side_effect=lambda *, tool_name, arguments: {
            "success": False,
            "error": "tool_timeout",
        }
    )
    monkeypatch.setattr(nodes, "call_llm", mock_call_llm)
    monkeypatch.setattr(nodes, "execute_tool", mock_execute_tool)

    result = graph.invoke(_initial_state(max_retries=2), config={"recursion_limit": 25})

    assert mock_execute_tool.call_count == 3
    assert mock_call_llm.call_count == 3
    assert result["retry_count"] == 2
    assert result["recovery_strategy"] == "abort"
    assert result["final_answer"] == "当前任务无法可靠完成，请稍后重试或补充更多信息。"
    assert result["messages"][-1]["content"] == result["final_answer"]

    recovery_contents = [message["content"] for message in _recovery_messages(result)]
    assert len(recovery_contents) == 2
    assert any("第 1 次重试" in content for content in recovery_contents)
    assert any("第 2 次重试" in content for content in recovery_contents)
    assert all("第 3 次重试" not in content for content in recovery_contents)


def test_player_not_found_routes_to_clarify(monkeypatch) -> None:
    mock_call_llm = Mock(side_effect=[_tool_call_response("call_test_1")])
    mock_execute_tool = Mock(
        return_value={"success": False, "error": "player_not_found"}
    )
    monkeypatch.setattr(nodes, "call_llm", mock_call_llm)
    monkeypatch.setattr(nodes, "execute_tool", mock_execute_tool)

    result = graph.invoke(_initial_state(), config={"recursion_limit": 10})

    assert mock_execute_tool.call_count == 1
    assert mock_call_llm.call_count == 1
    assert result["retry_count"] == 0
    assert result["recovery_strategy"] == "clarify"
    assert "确认球员姓名" in result["final_answer"]
    assert "昵称" in result["final_answer"]
    assert result["messages"][-1]["content"] == result["final_answer"]
    assert _recovery_messages(result) == []
