import sys
from types import SimpleNamespace

import pytest

from agent.rag import embedder, reranker


@pytest.fixture(autouse=True)
def reset_cached_models(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(embedder, "_model", None)
    monkeypatch.setattr(reranker, "_reranker", None)


def test_embedding_model_prefers_configured_local_path(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_path = tmp_path / "bge-small-zh-v1.5"
    model_path.mkdir()
    calls = []

    class FakeSentenceTransformer:
        def __init__(self, model_name: str, local_files_only: bool = False):
            calls.append((model_name, local_files_only))

    monkeypatch.setenv("EMBEDDING_MODEL_PATH", str(model_path))
    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(SentenceTransformer=FakeSentenceTransformer),
    )

    model = embedder.get_model()

    assert isinstance(model, FakeSentenceTransformer)
    assert calls == [(str(model_path), True)]
    assert embedder.MODEL_NAME not in calls[0]


def test_reranker_prefers_configured_local_path(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model_path = tmp_path / "bge-reranker-base"
    model_path.mkdir()
    calls = []

    class FakeCrossEncoder:
        def __init__(self, model_name: str, local_files_only: bool = False):
            calls.append((model_name, local_files_only))

    monkeypatch.setenv("RERANKER_MODEL_PATH", str(model_path))
    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(CrossEncoder=FakeCrossEncoder),
    )

    model = reranker.get_reranker()

    assert isinstance(model, FakeCrossEncoder)
    assert calls == [(str(model_path), True)]
    assert reranker.RERANKER_MODEL_NAME not in calls[0]


@pytest.mark.parametrize(
    ("module", "env_name", "getter_name"),
    [
        (embedder, "EMBEDDING_MODEL_PATH", "get_model"),
        (reranker, "RERANKER_MODEL_PATH", "get_reranker"),
    ],
)
def test_configured_missing_path_fails_without_network_fallback(
    module, env_name: str, getter_name: str, tmp_path, monkeypatch
) -> None:
    missing_path = tmp_path / "missing-model"
    monkeypatch.setenv(env_name, str(missing_path))

    with pytest.raises(FileNotFoundError, match=env_name):
        getattr(module, getter_name)()


def test_embedding_model_keeps_development_fallback(monkeypatch) -> None:
    calls = []

    class FakeSentenceTransformer:
        def __init__(self, model_name: str):
            calls.append(model_name)

    monkeypatch.delenv("EMBEDDING_MODEL_PATH", raising=False)
    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(SentenceTransformer=FakeSentenceTransformer),
    )

    embedder.get_model()

    assert calls == [embedder.MODEL_NAME]


def test_reranker_keeps_development_fallback(monkeypatch) -> None:
    calls = []

    class FakeCrossEncoder:
        def __init__(self, model_name: str):
            calls.append(model_name)

    monkeypatch.delenv("RERANKER_MODEL_PATH", raising=False)
    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(CrossEncoder=FakeCrossEncoder),
    )

    reranker.get_reranker()

    assert calls == [reranker.RERANKER_MODEL_NAME]


@pytest.mark.parametrize(
    ("module", "env_name", "class_name", "getter_name", "model_name"),
    [
        (
            embedder,
            "EMBEDDING_MODEL_PATH",
            "SentenceTransformer",
            "get_model",
            embedder.MODEL_NAME,
        ),
        (
            reranker,
            "RERANKER_MODEL_PATH",
            "CrossEncoder",
            "get_reranker",
            reranker.RERANKER_MODEL_NAME,
        ),
    ],
)
@pytest.mark.parametrize(
    "offline_env_name", ["HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"]
)
def test_offline_mode_makes_development_fallback_local_only(
    module,
    env_name: str,
    class_name: str,
    getter_name: str,
    model_name: str,
    offline_env_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    class FakeModel:
        def __init__(self, source: str, local_files_only: bool = False):
            calls.append((source, local_files_only))

    monkeypatch.delenv(env_name, raising=False)
    for name in module.OFFLINE_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(offline_env_name, "1")
    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(**{class_name: FakeModel}),
    )

    getattr(module, getter_name)()

    assert calls == [(model_name, True)]
