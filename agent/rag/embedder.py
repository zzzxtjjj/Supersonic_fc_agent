MODEL_NAME = "BAAI/bge-small-zh-v1.5"

_model = None


def get_model():
    global _model

    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)

    return _model


def embed_text(text: str) -> list[float]:
    model = get_model()
    vector = model.encode(text)

    return vector.tolist()
