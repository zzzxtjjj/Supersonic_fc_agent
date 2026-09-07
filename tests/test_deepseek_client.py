from agent.llm import openrouter_client


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}


def test_call_llm_uses_configured_provider_without_changing_tool_payload(
    monkeypatch,
) -> None:
    captured: dict = {}

    def fake_post(url, *, headers, json, timeout):
        captured.update(url=url, headers=headers, payload=json, timeout=timeout)
        return _FakeResponse()

    monkeypatch.setenv("LLM_API_KEY", "test-qwen-key")
    monkeypatch.setenv(
        "LLM_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    monkeypatch.setenv("LLM_MODEL", "qwen-flash")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "legacy-key-must-not-win")
    monkeypatch.setattr(openrouter_client.requests, "post", fake_post)

    messages = [{"role": "user", "content": "test"}]
    tools = [{"type": "function", "function": {"name": "test_tool"}}]
    result = openrouter_client.call_llm(messages=messages, tools=tools)

    assert captured["url"] == (
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    )
    assert captured["headers"]["Authorization"] == "Bearer test-qwen-key"
    assert captured["payload"] == {
        "model": "qwen-flash",
        "messages": messages,
        "tools": tools,
    }
    assert captured["timeout"] == 60
    assert result["choices"][0]["message"]["content"] == "ok"


def test_legacy_deepseek_key_uses_legacy_provider_defaults(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url, *, headers, json, timeout):
        captured.update(url=url, headers=headers, payload=json, timeout=timeout)
        return _FakeResponse()

    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "legacy-key")
    monkeypatch.setattr(openrouter_client.requests, "post", fake_post)

    openrouter_client.call_llm(messages=[{"role": "user", "content": "test"}])

    assert captured["url"] == "https://api.deepseek.com/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer legacy-key"
    assert captured["payload"]["model"] == "deepseek-v4-flash"
    assert "tools" not in captured["payload"]
