from agent.rag import embedder
from agent.rag.similarity import cosine_similarity


class FakeVector(list):
    def tolist(self) -> list[float]:
        return list(self)


class FakeEmbeddingModel:
    def encode(self, text: str) -> FakeVector:
        vectors = {
            "相近文本一": FakeVector([1.0, 0.9, 0.0]),
            "相近文本二": FakeVector([0.9, 1.0, 0.0]),
            "无关文本": FakeVector([0.0, 0.0, 1.0]),
        }
        return vectors[text]


def test_embedding_similarity_without_loading_external_model(monkeypatch) -> None:
    monkeypatch.setattr(embedder, "_model", FakeEmbeddingModel())

    vector_a = embedder.embed_text("相近文本一")
    vector_b = embedder.embed_text("相近文本二")
    vector_c = embedder.embed_text("无关文本")

    assert cosine_similarity(vector_a, vector_b) > 0.99
    assert cosine_similarity(vector_a, vector_c) == 0.0
