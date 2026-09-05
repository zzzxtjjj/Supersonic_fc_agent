import sys
from types import ModuleType
from unittest.mock import Mock
from unittest.mock import patch


def _unexpected_external_call(*args, **kwargs):
    raise AssertionError("Grounding tests must not call production LLM or tools.")


# Keep test collection offline: nodes.py imports both modules at import time.
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


def _initial_state(
    question: str = "火星梅西25-26赛季进了几个球？",
    *,
    max_grounding_retries: int = 2,
) -> dict:
    return {
        "messages": [
            {"role": "system", "content": "test system prompt"},
            {"role": "user", "content": question},
        ],
        "step": 0,
        "max_steps": 5,
        "retry_count": 0,
        "max_retries": 2,
        "grounding_retry_count": 0,
        "max_grounding_retries": max_grounding_retries,
        "final_answer": None,
        "verification_status": "pending",
        "verification_reason": None,
        "evidence_status": "pending",
        "evidence_reason": None,
        "recovery_strategy": None,
    }


def _direct_answer(content: str) -> dict:
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


def _goals_tool_call(name: str, call_id: str = "call_goals_1") -> dict:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": "get_player_goals",
                                "arguments": (
                                    f'{{"name":"{name}","season":"25-26"}}'
                                ),
                            },
                        }
                    ],
                }
            }
        ]
    }


def _grounding_messages(result: dict) -> list[dict]:
    return [
        message
        for message in result["messages"]
        if message.get("role") == "system"
        and "没有经过工具或知识库验证" in message.get("content", "")
    ]


def test_ungrounded_direct_fact_answer_is_rejected(monkeypatch) -> None:
    mock_call_llm = Mock(
        side_effect=[
            _direct_answer("火星梅西25-26赛季进了8球。"),
            _goals_tool_call("火星梅西"),
        ]
    )
    mock_execute_tool = Mock(
        return_value={"success": False, "error": "player_not_found"}
    )
    monkeypatch.setattr(nodes, "call_llm", mock_call_llm)
    monkeypatch.setattr(nodes, "execute_tool", mock_execute_tool)

    result = graph.invoke(_initial_state(), config={"recursion_limit": 15})

    assert mock_call_llm.call_count == 2
    mock_execute_tool.assert_called_once_with(
        tool_name="get_player_goals",
        arguments='{"name":"火星梅西","season":"25-26"}',
    )
    assert result["grounding_retry_count"] == 1
    assert len(_grounding_messages(result)) == 1
    assert result["recovery_strategy"] == "clarify"
    assert "确认球员姓名" in result["final_answer"]
    assert "8球" not in result["final_answer"]


def test_verified_final_answer_can_end(monkeypatch) -> None:
    mock_call_llm = Mock(
        side_effect=[
            _goals_tool_call("张谢童甲"),
            _direct_answer("张谢童甲25-26赛季进了3个球。"),
        ]
    )
    mock_execute_tool = Mock(
        return_value={
            "success": True,
            "name": "张谢童甲",
            "season": "25-26",
            "goals": 3,
        }
    )
    monkeypatch.setattr(nodes, "call_llm", mock_call_llm)
    monkeypatch.setattr(nodes, "execute_tool", mock_execute_tool)

    result = graph.invoke(
        _initial_state("张谢童甲25-26赛季进了几个球？"),
        config={"recursion_limit": 12},
    )

    assert mock_call_llm.call_count == 2
    assert result["verification_status"] == "passed"
    assert result["evidence_status"] == "supported"
    assert result["grounding_retry_count"] == 0
    assert _grounding_messages(result) == []
    assert result["messages"][-1]["content"] == "张谢童甲25-26赛季进了3个球。"


def test_repeated_ungrounded_answers_reach_safe_abort(monkeypatch) -> None:
    mock_call_llm = Mock(
        return_value=_direct_answer("火星梅西25-26赛季进了8球。")
    )
    mock_execute_tool = Mock(side_effect=_unexpected_external_call)
    monkeypatch.setattr(nodes, "call_llm", mock_call_llm)
    monkeypatch.setattr(nodes, "execute_tool", mock_execute_tool)

    result = graph.invoke(
        _initial_state(max_grounding_retries=2),
        config={"recursion_limit": 15},
    )

    assert mock_call_llm.call_count == 3
    mock_execute_tool.assert_not_called()
    assert result["grounding_retry_count"] == 2
    assert len(_grounding_messages(result)) == 2
    assert result["recovery_strategy"] == "abort"
    assert "8球" not in result["final_answer"]


def _assert_direct_answer_without_grounding(
    monkeypatch,
    question: str,
    answer: str,
) -> dict:
    mock_call_llm = Mock(return_value=_direct_answer(answer))
    mock_execute_tool = Mock(side_effect=_unexpected_external_call)
    monkeypatch.setattr(nodes, "call_llm", mock_call_llm)
    monkeypatch.setattr(nodes, "execute_tool", mock_execute_tool)

    result = graph.invoke(_initial_state(question), config={"recursion_limit": 5})

    mock_call_llm.assert_called_once()
    mock_execute_tool.assert_not_called()
    assert result["evidence_status"] == "pending"
    assert result["grounding_retry_count"] == 0
    assert result["messages"][-1]["content"] == answer
    return result


def test_agent_meta_greeting_can_end_without_evidence(monkeypatch) -> None:
    _assert_direct_answer_without_grounding(
        monkeypatch,
        "你好，你是谁？",
        "你好！我是超音速足球队 AI Agent。",
    )


def test_agent_capability_query_can_end_without_evidence(monkeypatch) -> None:
    _assert_direct_answer_without_grounding(
        monkeypatch,
        "你能做什么？",
        "我可以帮你查询已有的球队资料。",
    )


def _assert_player_identity_is_grounded(monkeypatch, question: str) -> None:
    mock_call_llm = Mock(
        side_effect=[
            _direct_answer("这是一条未经验证的球员介绍。"),
            _goals_tool_call("张谢童甲"),
        ]
    )
    mock_execute_tool = Mock(
        return_value={"success": False, "error": "player_not_found"}
    )
    monkeypatch.setattr(nodes, "call_llm", mock_call_llm)
    monkeypatch.setattr(nodes, "execute_tool", mock_execute_tool)

    result = graph.invoke(_initial_state(question), config={"recursion_limit": 12})

    assert mock_call_llm.call_count == 2
    assert mock_execute_tool.call_count == 1
    assert result["grounding_retry_count"] == 1
    assert len(_grounding_messages(result)) == 1
    assert result["recovery_strategy"] == "clarify"


def test_player_identity_query_still_requires_grounding(monkeypatch) -> None:
    _assert_player_identity_is_grounded(monkeypatch, "张谢童甲是谁？")


def test_greeting_before_player_identity_does_not_bypass_grounding(monkeypatch) -> None:
    _assert_player_identity_is_grounded(monkeypatch, "你好，张谢童甲是谁？")


def test_plain_small_talk_can_end_without_evidence(monkeypatch) -> None:
    _assert_direct_answer_without_grounding(
        monkeypatch,
        "你好",
        "你好！我是超音速足球队 AI Agent。",
    )
