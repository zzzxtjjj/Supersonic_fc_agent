from fastapi.testclient import TestClient

from backend.api import agent as agent_api
from backend.main import app


def test_agent_chat_calls_product_agent_and_returns_answer(monkeypatch) -> None:
    calls: list[str] = []

    def fake_agent(question: str) -> str:
        calls.append(question)
        return "张谢童甲在25-26赛季进了3个球。"

    monkeypatch.setattr(agent_api, "run_graph_agent", fake_agent)

    with TestClient(app) as client:
        response = client.post(
            "/api/agent/chat",
            json={"message": "  张谢童甲25-26赛季进了几个球？  "},
        )

    assert response.status_code == 200
    assert calls == ["张谢童甲25-26赛季进了几个球？"]
    payload = response.json()
    assert payload["answer"] == "张谢童甲在25-26赛季进了3个球。"
    assert isinstance(payload["session_id"], str)
    assert payload["sources"] == []


def test_agent_chat_preserves_client_session_id(monkeypatch) -> None:
    monkeypatch.setattr(agent_api, "run_graph_agent", lambda question: "你好。")

    with TestClient(app) as client:
        response = client.post(
            "/api/agent/chat",
            json={"message": "你好", "session_id": "browser-session"},
        )

    assert response.status_code == 200
    assert response.json()["session_id"] == "browser-session"


def test_agent_chat_exception_returns_only_safe_error(monkeypatch) -> None:
    def failing_agent(question: str) -> str:
        del question
        raise RuntimeError(
            "provider failure Authorization=secret C:\\private\\agent.py"
        )

    monkeypatch.setattr(agent_api, "run_graph_agent", failing_agent)

    with TestClient(app) as client:
        response = client.post(
            "/api/agent/chat",
            json={"message": "测试失败处理"},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": agent_api.SAFE_AGENT_ERROR}
    response_text = response.text.lower()
    assert "authorization" not in response_text
    assert "secret" not in response_text
    assert "private" not in response_text


def test_agent_chat_response_does_not_expose_internal_state(monkeypatch) -> None:
    monkeypatch.setattr(agent_api, "run_graph_agent", lambda question: "安全回答")

    with TestClient(app) as client:
        response = client.post(
            "/api/agent/chat",
            json={"message": "你好，你是谁？"},
        )

    assert response.status_code == 200
    assert set(response.json()) == {"answer", "session_id", "sources"}
    forbidden = {
        "trace",
        "tool_trace",
        "reasoning",
        "reasoning_details",
        "messages",
        "system_prompt",
        "api_key",
    }
    assert forbidden.isdisjoint(response.json())


def test_agent_chat_rejects_empty_or_blank_message(monkeypatch) -> None:
    calls = 0

    def fake_agent(question: str) -> str:
        nonlocal calls
        calls += 1
        return question

    monkeypatch.setattr(agent_api, "run_graph_agent", fake_agent)

    with TestClient(app) as client:
        empty = client.post("/api/agent/chat", json={"message": ""})
        blank = client.post("/api/agent/chat", json={"message": "   "})

    assert empty.status_code == 422
    assert blank.status_code == 422
    assert calls == 0
