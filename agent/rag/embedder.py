import inspect
import os
from pathlib import Path


MODEL_NAME = "BAAI/bge-small-zh-v1.5"
MODEL_PATH_ENV = "EMBEDDING_MODEL_PATH"
OFFLINE_ENV_VARS = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")

_model = None


def _model_source() -> tuple[str, bool]:
    configured_path = os.getenv(MODEL_PATH_ENV, "").strip()
    if not configured_path:
        return MODEL_NAME, False

    model_path = Path(configured_path).expanduser()
    if not model_path.is_dir():
        raise FileNotFoundError(
            f"{MODEL_PATH_ENV} does not point to a model directory: {model_path}"
        )

    return str(model_path), True


def _supports_local_files_only(model_class: type) -> bool:
    try:
        return "local_files_only" in inspect.signature(model_class).parameters
    except (TypeError, ValueError):
        return False


def _offline_mode_enabled() -> bool:
    true_values = {"1", "true", "yes", "on"}
    return any(
        os.getenv(name, "").strip().lower() in true_values
        for name in OFFLINE_ENV_VARS
    )


def get_model():
    global _model

    if _model is None:
        model_source, is_local_path = _model_source()

        from sentence_transformers import SentenceTransformer

        kwargs = {}
        local_only = is_local_path or _offline_mode_enabled()
        if local_only and _supports_local_files_only(SentenceTransformer):
            kwargs["local_files_only"] = True

        _model = SentenceTransformer(model_source, **kwargs)

    return _model


def embed_text(text: str) -> list[float]:
    model = get_model()
    vector = model.encode(text)

    return vector.tolist()
