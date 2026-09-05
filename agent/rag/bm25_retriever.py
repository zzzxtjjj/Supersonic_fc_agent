from agent.rag.loader import load_chunks
from agent.rag.tokenizer import tokenize
from agent.rag.bm25_basics import bm25_query_score
from agent.rag.filters import match_metadata


def build_search_text(chunk: dict) -> str:
    title = chunk["metadata"]["title"]
    text = chunk["text"]
    keywords = chunk["metadata"]["keywords"]

    keywords_text = " ".join(keywords)

    search_text = f"{title} {text} {keywords_text}"

    return search_text


def bm25_search(
    query: str,
    top_k: int = 3,
    filters: dict | None = None
) -> list[dict]:

    chunks = load_chunks()

    if filters is not None:
        filtered_chunks = []

        for chunk in chunks:
            if match_metadata(chunk["metadata"], filters):
                filtered_chunks.append(chunk)

        chunks = filtered_chunks

    if not chunks:
        return []

    # 1. 把用户问题分词
    query_tokens = tokenize(query)
    
    # 2. 把 chunk 分词
    tokenized_documents = []

    for chunk in chunks:
        search_text = build_search_text(chunk)
        document_tokens = tokenize(search_text)
        tokenized_documents.append(document_tokens)

    results = []

    # 3. 对每一个 chunk 计算 BM25
    for index, chunk in enumerate(chunks):
        document_tokens = tokenized_documents[index]

        score = bm25_query_score(
            query=query_tokens,
            document=document_tokens,
            documents=tokenized_documents
        )

        results.append(
            {
                "score": score,
                "chunk": chunk
            }
        )

    results = [
        result
        for result in results
        if result["score"] > 0
    ]

    # 4. 从高到低排序
    results.sort(
        key=lambda result: result["score"],
        reverse=True
    )

    # 5. 返回 Top-K
    return results[:top_k]


if __name__ == "__main__":
    results = bm25_search(
        "干宸浩有什么技术特点？",
        top_k=3,
        filters={
            "player": "干宸浩"
        }
    )

    for result in results:
        print("=" * 80)
        print("Score:", result["score"])
        print("ID:", result["chunk"]["id"])
        print("Title:", result["chunk"]["metadata"]["title"])
        print("Text:", result["chunk"]["text"])