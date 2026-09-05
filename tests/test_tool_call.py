import json

from agent.core import agent_loop


def test_legacy_agent_loop_pairs_tool_result_without_live_provider(monkeypatch) -> None:
    responses = iter(
        [
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-test",
                                    "type": "function",
                                    "function": {
                                        "name": "get_player_goals",
                                        "arguments": json.dumps(
                                            {"name": "张谢童甲", "season": "25-26"},
                                            ensure_ascii=False,
                                        ),
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "张谢童甲在25-26赛季进了3个球。",
                        }
                    }
                ]
            },
        ]
    )
    observed_messages: list[list[dict]] = []

    def fake_llm(messages: list[dict], tools: list[dict]) -> dict:
        assert tools is agent_loop.TOOL_SCHEMAS
        observed_messages.append(list(messages))
        return next(responses)

    monkeypatch.setattr(agent_loop, "call_llm", fake_llm)

    answer = agent_loop.run_agent("张谢童甲25-26赛季射手榜排第几？")

    assert answer == "张谢童甲在25-26赛季进了3个球。"
    tool_messages = [
        message
        for message in observed_messages[-1]
        if message.get("role") == "tool"
    ]
    assert tool_messages[0]["tool_call_id"] == "call-test"
    assert json.loads(tool_messages[0]["content"])["goals"] == 3
