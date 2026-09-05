from agent.llm import openrouter_client


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}


def test_call_llm_uses_deepseek_without_changing_tool_payload(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url, *, headers, json, timeout):
        captured.update(url=url, headers=headers, payload=json, timeout=timeout)
        return _FakeResponse()

    monkeypatch.setattr(openrouter_client, "DEEPSEEK_API_KEY", "test-deepseek-key")
    monkeypatch.setattr(openrouter_client.requests, "post", fake_post)

    messages = [{"role": "user", "content": "test"}]
    tools = [{"type": "function", "function": {"name": "test_tool"}}]
    result = openrouter_client.call_llm(messages=messages, tools=tools)

    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer test-deepseek-key"
    assert captured["payload"] == {
        "model": "deepseek-v4-flash",
        "messages": messages,
        "tools": tools,
    }
    assert captured["timeout"] == 60
    assert result["choices"][0]["message"]["content"] == "ok"
