import os

import requests
from dotenv import load_dotenv


load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_llm(messages: list, tools: list | None = None) -> dict:
    """
    调用 OpenRouter LLM。

    messages:
        对话消息列表

    tools:
        提供给模型的 Tool Schema 列表
    """

    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openrouter/free",
        "messages": messages,
    }

    if tools is not None:
        payload["tools"] = tools

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()