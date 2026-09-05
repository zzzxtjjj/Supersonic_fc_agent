import sys
from types import ModuleType
from unittest.mock import Mock, patch


def _unexpected_external_call(*args, **kwargs):
    raise AssertionError("Graph smoke test must not call production LLM or tools.")


# nodes.py imports the production LLM client and complete tool registry at import
# time. Stub both modules so collecting this test never loads OpenRouter or RAG.
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
    from agent.workflow import run_graph
    from agent.workflow.graph import graph


def _initial_state() -> dict:
    return {
        "messages": [
            {"role": "system", "content": "test system prompt"},
            {
                "role": "user",
                "content": "张谢童甲25-26赛季进了几个球？",
            },
        ],
        "step": 0,
        "max_steps": 5,
        "retry_count": 0,
        "max_retries": 2,
        "grounding_retry_count": 0,
        "max_grounding_retries": 2,
        "final_answer": None,
        "verification_status": "pending",
        "verification_reason": None,
        "evidence_status": "pending",
        "evidence_reason": None,
        "recovery_strategy": None,
    }


def _tool_call_response() -> dict:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_goals_1",
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


def _final_response() -> dict:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "张谢童甲25-26赛季进了3个球。",
                }
            }
        ]
    }


def test_graph_tool_success_evidence_supported_then_final(monkeypatch) -> None:
    mock_call_llm = Mock(side_effect=[_tool_call_response(), _final_response()])
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

    result = graph.invoke(_initial_state(), config={"recursion_limit": 12})

    assert mock_call_llm.call_count == 2
    mock_execute_tool.assert_called_once_with(
        tool_name="get_player_goals",
        arguments='{"name":"张谢童甲","season":"25-26"}',
    )
    assert result["verification_status"] == "passed"
    assert result["evidence_status"] == "supported"
    assert result["messages"][-1]["content"] == "张谢童甲25-26赛季进了3个球。"


def test_max_steps_tool_call_routes_to_safe_abort(monkeypatch) -> None:
    mock_call_llm = Mock(return_value=_tool_call_response())
    mock_execute_tool = Mock(side_effect=_unexpected_external_call)
    monkeypatch.setattr(nodes, "call_llm", mock_call_llm)
    monkeypatch.setattr(nodes, "execute_tool", mock_execute_tool)
    state = _initial_state()
    state["max_steps"] = 0

    result = graph.invoke(state, config={"recursion_limit": 6})

    mock_execute_tool.assert_not_called()
    assert result["recovery_strategy"] == "abort"
    assert isinstance(result["final_answer"], str)
    assert result["final_answer"]
    assert result["messages"][-1]["content"] == result["final_answer"]


def test_evidence_insufficient_ends_with_text_answer(monkeypatch) -> None:
    monkeypatch.setattr(nodes, "call_llm", Mock(return_value=_tool_call_response()))
    monkeypatch.setattr(
        nodes,
        "execute_tool",
        Mock(
            return_value={
                "success": True,
                "name": "其他球员",
                "season": "25-26",
                "goals": 3,
            }
        ),
    )

    result = graph.invoke(_initial_state(), config={"recursion_limit": 8})

    assert result["verification_status"] == "passed"
    assert result["evidence_status"] == "insufficient"
    assert isinstance(result["final_answer"], str)
    assert result["final_answer"]
    assert result["messages"][-1]["content"] == result["final_answer"]


def test_collect_recent_tool_records_matches_multiple_calls_in_order() -> None:
    state = {
        "messages": [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "get_player_goals",
                            "arguments": '{"name":"张谢童甲","season":"25-26"}',
                        },
                    },
                    {
                        "id": "call_2",
                        "function": {
                            "name": "get_player_number",
                            "arguments": '{"name":"干宸浩","season":"25-26"}',
                        },
                    },
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": (
                    '{"success":true,"name":"张谢童甲",'
                    '"season":"25-26","goals":3}'
                ),
            },
            {
                "role": "tool",
                "tool_call_id": "call_2",
                "content": (
                    '{"success":true,"name":"干宸浩",'
                    '"season":"25-26","number":6}'
                ),
            },
        ]
    }

    records = nodes.collect_recent_tool_records(state)

    assert [record["tool_call_id"] for record in records] == ["call_1", "call_2"]
    assert [record["tool_name"] for record in records] == [
        "get_player_goals",
        "get_player_number",
    ]
    assert records[0]["arguments"]["name"] == "张谢童甲"
    assert records[1]["result"]["number"] == 6


def test_collect_recent_tool_records_handles_malformed_and_unknown_calls() -> None:
    state = {
        "messages": [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "known",
                        "function": {
                            "name": "get_player_goals",
                            "arguments": "not-json",
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "known",
                "content": "[]",
            },
            {
                "role": "tool",
                "tool_call_id": "unknown",
                "content": "not-json",
            },
            {
                "role": "tool",
                "content": "not-json",
            },
        ]
    }

    records = nodes.collect_recent_tool_records(state)

    assert records == [
        {
            "tool_call_id": "known",
            "tool_name": "get_player_goals",
            "arguments": {},
            "result": {},
        }
    ]


def test_run_graph_agent_prefers_final_answer(monkeypatch) -> None:
    class InvokeGraph:
        def invoke(self, state):
            return {
                **state,
                "final_answer": "安全终止回答",
                "messages": state["messages"]
                + [{"role": "assistant", "content": None, "tool_calls": []}],
            }

    monkeypatch.setattr(run_graph, "graph", InvokeGraph())

    assert run_graph.run_graph_agent("test") == "安全终止回答"


def test_run_graph_agent_skips_tool_call_when_using_message_fallback(monkeypatch) -> None:
    class InvokeGraph:
        def invoke(self, state):
            return {
                **state,
                "final_answer": None,
                "messages": state["messages"]
                + [
                    {"role": "assistant", "content": "最近的可用文本"},
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{"id": "unfinished_call"}],
                    },
                ],
            }

    monkeypatch.setattr(run_graph, "graph", InvokeGraph())

    assert run_graph.run_graph_agent("test") == "最近的可用文本"


def test_trace_returns_text_and_filters_private_reasoning(monkeypatch, capsys) -> None:
    class StreamGraph:
        def stream(self, state, stream_mode):
            assert stream_mode == "values"
            yield {
                **state,
                "messages": state["messages"]
                + [
                    {
                        "role": "assistant",
                        "content": "最终文本",
                        "reasoning": "private",
                        "reasoning_details": {"private": True},
                    }
                ],
            }

    monkeypatch.setattr(run_graph, "graph", StreamGraph())

    answer = run_graph.trace_graph_agent("test")
    output = capsys.readouterr().out

    assert answer == "最终文本"
    assert "reasoning" not in output
    assert "reasoning_details" not in output
    assert "private" not in output
