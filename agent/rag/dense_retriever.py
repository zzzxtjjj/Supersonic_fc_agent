from agent.rag.loader import load_dense_index
from agent.rag.embedder import embed_text
from agent.rag.similarity import cosine_similarity
from agent.rag.filters import match_metadata


def dense_search(
    query: str,
    top_k: int = 3,
    filters: dict | None = None
) -> list[dict]:
    
    index = load_dense_index()

    if filters is not None:
        filtered_index = []

        for chunk in index:
            if match_metadata(chunk["metadata"], filters):
                filtered_index.append(chunk)

        index = filtered_index

    if not index:
        return []

    query_vector = embed_text(query)

    results = []

    for chunk in index:
        text = chunk["text"]

        chunk_vector = chunk["embedding"]

        score = cosine_similarity(query_vector, chunk_vector)

        results.append(
            {
                "score": score,
                "chunk": {
                    "id": chunk["id"],
                    "text": text,
                    "metadata": chunk["metadata"]
                }
            }
        )

    results.sort(
        key=lambda result: result["score"],
        reverse=True
    )

    return results[:top_k]


if __name__ == "__main__":
    results = dense_search(
        query="干宸浩有什么技术特点？",
        top_k=3,
        filters={
            "player": "干宸浩"
        }
    )

    for result in results:
        print("=" * 80)
        print("Score:", result["score"])
        print("Title:", result["chunk"]["metadata"]["title"])
        print("Player:", result["chunk"]["metadata"]["player"])