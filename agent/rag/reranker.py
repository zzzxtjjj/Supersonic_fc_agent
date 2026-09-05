from agent.rag.hybrid_retriever import hybrid_search


RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"

_reranker = None


def get_reranker():
    global _reranker

    if _reranker is None:
        from sentence_transformers import CrossEncoder

        _reranker = CrossEncoder(RERANKER_MODEL_NAME)

    return _reranker


def build_rerank_text(chunk: dict) -> str:
    title = chunk["metadata"]["title"]
    text = chunk["text"]

    return f"{title}\n{text}"


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 3
) -> list[dict]:

    if not candidates:
        return []

    model = get_reranker()

    pairs = []

    for candidate in candidates:
        chunk = candidate["chunk"]

        document = build_rerank_text(chunk)

        pairs.append(
            [query, document]
        )

    scores = model.predict(pairs)

    results = []

    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

        results.append(candidate)

    results.sort(
        key=lambda result: result["rerank_score"],
        reverse=True
    )

    return results[:top_k]


def retrieve_with_rerank(
    query: str,
    top_k: int = 3,
    candidate_k: int = 10,
    filters: dict | None = None
) -> list[dict]:

    candidates = hybrid_search(
        query=query,
        top_k=candidate_k,
        candidate_k=candidate_k,
        filters=filters
    )

    results = rerank(
        query=query,
        candidates=candidates,
        top_k=top_k
    )

    return results


if __name__ == "__main__":
    results = retrieve_with_rerank(
        query="干宸浩有什么技术特点？",
        top_k=3,
        candidate_k=10,
        filters={"player": "干宸浩"}
    )

    for result in results:
        print("=" * 80)
        print("Rerank Score:", result["rerank_score"])
        print("RRF Score:", result["rrf_score"])
        print("Dense Rank:", result["dense_rank"])
        print("BM25 Rank:", result["bm25_rank"])
        print("ID:", result["chunk"]["id"])
        print("Title:", result["chunk"]["metadata"]["title"])
        print("Text:", result["chunk"]["text"])
