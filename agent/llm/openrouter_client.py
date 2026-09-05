import os

import requests
from dotenv import load_dotenv


load_dotenv()


DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"


def call_llm(messages: list, tools: list | None = None) -> dict:
    """
    调用 DeepSeek LLM。

    messages:
        对话消息列表

    tools:
        提供给模型的 Tool Schema 列表
    """

    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY is not configured.")

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek-v4-flash",
        "messages": messages,
    }

    if tools is not None:
        payload["tools"] = tools

    response = requests.post(
        DEEPSEEK_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()
