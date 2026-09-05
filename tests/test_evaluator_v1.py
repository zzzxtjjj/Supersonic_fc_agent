from evals.evaluator_v1 import evaluate_case
from evals.actual_extractor import extract_actual


def test_structured_fact_passes():
    state = {
        "messages": [
            {
                "role": "user",
                "content": "张谢童甲25-26赛季进了几个球？",
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
                            ),
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_123",
                "content": (
                    '{"success":true,'
                    '"name":"张谢童甲",'
                    '"season":"25-26",'
                    '"goals":3}'
                ),
            },
            {
                "role": "assistant",
                "content": "张谢童甲在25-26赛季进了3个球。",
            },
        ],
        "final_answer": None,
        "recovery_strategy": None,
    }

    expected = {
        "answer_contains": ["张谢童甲", "3"],
        "tool_names": ["get_player_goals"],
        "workflow_outcome": "answer",
    }

    actual = extract_actual(state)
    result = evaluate_case(expected, actual)

    assert result["answer_contains_passed"] is True
    assert result["tool_selection_passed"] is True
    assert result["workflow_outcome_passed"] is True
    assert result["passed"] is True


def test_wrong_tool_fails():
    actual = {
        "final_answer": "张谢童甲在25-26赛季进了3个球。",
        "tool_names": ["get_player_number"],
        "workflow_outcome": "answer",
    }

    expected = {
        "answer_contains": ["张谢童甲", "3"],
        "tool_names": ["get_player_goals"],
        "workflow_outcome": "answer",
    }

    result = evaluate_case(expected, actual)

    assert result["answer_contains_passed"] is True
    assert result["tool_selection_passed"] is False
    assert result["passed"] is False


def test_clarify_outcome_passes():
    state = {
        "messages": [
            {
                "role": "user",
                "content": "火星梅西25-26赛季进了几个球？",
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_456",
                        "function": {
                            "name": "get_player_goals",
                            "arguments": (
                                '{"name":"火星梅西",'
                                '"season":"25-26"}'
                            ),
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_456",
                "content": (
                    '{"success":false,'
                    '"error":"player_not_found"}'
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "没有找到该球员。"
                    "请确认球员姓名是否正确，"
                    "或告诉我他的队内昵称。"
                ),
            },
        ],
        "final_answer": (
            "没有找到该球员。"
            "请确认球员姓名是否正确，"
            "或告诉我他的队内昵称。"
        ),
        "recovery_strategy": "clarify",
    }

    expected = {
        "answer_contains": ["没有找到"],
        "tool_names": ["get_player_goals"],
        "workflow_outcome": "clarify",
    }

    actual = extract_actual(state)
    result = evaluate_case(expected, actual)

    assert result["tool_selection_passed"] is True
    assert result["workflow_outcome_passed"] is True
    assert result["passed"] is True


def test_casual_query_uses_no_tool():
    state = {
        "messages": [
            {
                "role": "user",
                "content": "你好，你是谁？",
            },
            {
                "role": "assistant",
                "content": "你好！我是超音速足球队的 AI Agent。",
            },
        ],
        "final_answer": None,
        "recovery_strategy": None,
    }

    expected = {
        "answer_contains": ["超音速"],
        "tool_names": [],
        "workflow_outcome": "answer",
    }

    actual = extract_actual(state)
    result = evaluate_case(expected, actual)

    assert actual["tool_names"] == []
    assert result["tool_selection_passed"] is True
    assert result["workflow_outcome_passed"] is True
    assert result["passed"] is True