import copy
import json

from evals import agent_adapter


class FakeGraph:
    def __init__(self, updates: list[dict]):
        self.updates = updates
        self.received_state = None

    def stream(self, state: dict, stream_mode: str):
        assert stream_mode == "updates"
        self.received_state = copy.deepcopy(state)
        yield from self.updates


def _assistant_tool_call(name: str, call_id: str) -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(
                        {
                            "name": "不应进入 trace",
                            "reasoning": "private",
                        },
                        ensure_ascii=False,
                    ),
                },
            }
        ],
    }


def _run_with_fake_graph(monkeypatch, updates: list[dict], question: str) -> dict:
    fake_graph = FakeGraph(updates)
    monkeypatch.setattr(
        agent_adapter,
        "_load_runtime",
        lambda: (fake_graph, "private system prompt that must not enter trace"),
    )
    result = agent_adapter.run_agent_for_eval(question)
    assert fake_graph.received_state["messages"][1]["content"] == question
    return result


def test_successful_goals_query_has_structured_trace(monkeypatch) -> None:
    initial_messages = [
        {"role": "system", "content": "private system prompt that must not enter trace"},
        {"role": "user", "content": "张谢童甲进了几个球？"},
    ]
    tool_call = _assistant_tool_call("get_player_goals", "call-1")
    tool_message = {
        "role": "tool",
        "tool_call_id": "call-1",
        "content": json.dumps(
            {
                "success": True,
                "goals": 3,
                "reasoning_details": "private",
                "api_key": "private",
            }
        ),
    }
    final_message = {
        "role": "assistant",
        "content": "张谢童甲进了3个球。",
        "reasoning": "private",
    }
    updates = [
        {"llm_node": {"messages": initial_messages + [tool_call]}},
        {"tool_node": {"messages": initial_messages + [tool_call, tool_message], "step": 1}},
        {"verify_tool_results_node": {"verification_status": "passed", "verification_reason": None}},
        {"verify_evidence_node": {"evidence_status": "supported", "evidence_reason": None}},
        {"llm_node": {"messages": initial_messages + [tool_call, tool_message, final_message]}},
    ]

    result = _run_with_fake_graph(monkeypatch, updates, "张谢童甲进了几个球？")

    assert result == {
        "final_answer": "张谢童甲进了3个球。",
        "trace": [
            {"event": "tool_call", "tool_name": "get_player_goals"},
            {"event": "tool_result", "tool_name": "get_player_goals", "success": True},
            {"event": "execution_verification", "status": "passed"},
            {"event": "evidence_verification", "status": "supported"},
            {"event": "workflow_end", "outcome": "answer"},
        ],
    }
    serialized = json.dumps(result, ensure_ascii=False)
    assert "private" not in serialized
    assert "arguments" not in serialized
    assert "reasoning" not in serialized


def test_unknown_player_trace_ends_with_clarify(monkeypatch) -> None:
    initial_messages = [
        {"role": "system", "content": "private system prompt"},
        {"role": "user", "content": "火星梅西进了几个球？"},
    ]
    tool_call = _assistant_tool_call("get_player_goals", "call-2")
    tool_message = {
        "role": "tool",
        "tool_call_id": "call-2",
        "content": '{"success": false, "error": "player_not_found"}',
    }
    clarify_message = {"role": "assistant", "content": "没有找到该球员。"}
    updates = [
        {"llm_node": {"messages": initial_messages + [tool_call]}},
        {"tool_node": {"messages": initial_messages + [tool_call, tool_message], "step": 1}},
        {"verify_tool_results_node": {"verification_status": "failed", "verification_reason": "player_not_found"}},
        {"clarify_node": {"messages": initial_messages + [tool_call, tool_message, clarify_message], "final_answer": "没有找到该球员。", "recovery_strategy": "clarify"}},
    ]

    result = _run_with_fake_graph(monkeypatch, updates, "火星梅西进了几个球？")

    assert result["trace"] == [
        {"event": "tool_call", "tool_name": "get_player_goals"},
        {"event": "tool_result", "tool_name": "get_player_goals", "success": False},
        {"event": "execution_verification", "status": "failed"},
        {"event": "workflow_end", "outcome": "clarify"},
    ]


def test_agent_meta_query_has_only_answer_end_event(monkeypatch) -> None:
    final_message = {"role": "assistant", "content": "我是超音速足球队 AI Agent。"}
    updates = [
        {
            "llm_node": {
                "messages": [
                    {"role": "system", "content": "private system prompt"},
                    {"role": "user", "content": "你好，你是谁？"},
                    final_message,
                ]
            }
        }
    ]

    result = _run_with_fake_graph(monkeypatch, updates, "你好，你是谁？")

    assert result["trace"] == [{"event": "workflow_end", "outcome": "answer"}]


def test_abort_has_one_abort_end_event(monkeypatch) -> None:
    abort_message = {"role": "assistant", "content": "当前任务无法可靠完成。"}
    updates = [
        {
            "abort_node": {
                "messages": [abort_message],
                "final_answer": abort_message["content"],
                "recovery_strategy": "abort",
            }
        }
    ]

    result = _run_with_fake_graph(monkeypatch, updates, "test abort")

    end_events = [item for item in result["trace"] if item["event"] == "workflow_end"]
    assert end_events == [{"event": "workflow_end", "outcome": "abort"}]


def test_grounding_recovery_is_recorded_only_when_node_runs(monkeypatch) -> None:
    updates = [
        {"grounding_recovery_node": {"grounding_retry_count": 1}},
        {
            "abort_node": {
                "messages": [{"role": "assistant", "content": "safe abort"}],
                "final_answer": "safe abort",
                "recovery_strategy": "abort",
            }
        },
    ]

    result = _run_with_fake_graph(monkeypatch, updates, "team fact")

    assert result["trace"] == [
        {"event": "grounding_recovery"},
        {"event": "workflow_end", "outcome": "abort"},
    ]
