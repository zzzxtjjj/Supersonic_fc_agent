import os

import requests
from dotenv import load_dotenv


load_dotenv()


DEFAULT_LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_LLM_MODEL = "qwen-flash"
LEGACY_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
LEGACY_DEEPSEEK_MODEL = "deepseek-v4-flash"


def _get_llm_config() -> tuple[str, str, str]:
    configured_key = os.getenv("LLM_API_KEY")
    legacy_key = os.getenv("DEEPSEEK_API_KEY")
    api_key = configured_key or legacy_key

    if not api_key:
        raise ValueError("LLM_API_KEY is not configured.")

    use_legacy_defaults = not configured_key and bool(legacy_key)
    base_url = os.getenv("LLM_BASE_URL") or (
        LEGACY_DEEPSEEK_BASE_URL
        if use_legacy_defaults
        else DEFAULT_LLM_BASE_URL
    )
    model = os.getenv("LLM_MODEL") or (
        LEGACY_DEEPSEEK_MODEL if use_legacy_defaults else DEFAULT_LLM_MODEL
    )
    return api_key, base_url.rstrip("/"), model


def _chat_completions_url(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def call_llm(messages: list, tools: list | None = None) -> dict:
    """
    调用 OpenAI-compatible Chat Completions API。

    messages:
        对话消息列表

    tools:
        提供给模型的 Tool Schema 列表
    """

    api_key, base_url, model = _get_llm_config()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    if tools is not None:
        payload["tools"] = tools

    response = requests.post(
        _chat_completions_url(base_url),
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()
