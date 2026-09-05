from agent.rag.dense_retriever import dense_search
from agent.rag.bm25_retriever import bm25_search


def hybrid_search(
    query: str,
    top_k: int = 3,
    candidate_k: int = 10,
    rrf_k: int = 60,
    filters: dict | None = None
) -> list[dict]:

    dense_results = dense_search(
        query,
        top_k=candidate_k,
        filters=filters
    )

    bm25_results = bm25_search(
        query,
        top_k=candidate_k,
        filters=filters
    )

    fused_results = {}

    # Dense 排名加入 RRF
    for rank, result in enumerate(dense_results, start=1):
        chunk = result["chunk"]
        chunk_id = chunk["id"]

        if chunk_id not in fused_results:
            fused_results[chunk_id] = {
                "chunk": chunk,
                "rrf_score": 0.0,
                "dense_rank": None,
                "bm25_rank": None
            }

        fused_results[chunk_id]["rrf_score"] += 1 / (rrf_k + rank)

        fused_results[chunk_id]["dense_rank"] = rank

    # BM25 排名加入 RRF
    for rank, result in enumerate(bm25_results, start=1):
        chunk = result["chunk"]
        chunk_id = chunk["id"]

        if chunk_id not in fused_results:
            fused_results[chunk_id] = {
                "chunk": chunk,
                "rrf_score": 0.0,
                "dense_rank": None,
                "bm25_rank": None
            }

        fused_results[chunk_id]["rrf_score"] += 1 / (rrf_k + rank)

        fused_results[chunk_id]["bm25_rank"] = rank

    results = list(fused_results.values())

    results.sort(
        key=lambda result: result["rrf_score"],
        reverse=True
    )

    return results[:top_k]

if __name__ == "__main__":
    results = hybrid_search(
        "干宸浩有什么技术特点？",
        top_k=3,
        filters={
        "player": "干宸浩"
    }
    )

    for result in results:
        print("=" * 80)
        print("RRF Score:", result["rrf_score"])
        print("Dense Rank:", result["dense_rank"])
        print("BM25 Rank:", result["bm25_rank"])
        print("ID:", result["chunk"]["id"])
        print("Title:", result["chunk"]["metadata"]["title"])