def build_context(results: list[dict]) -> str:

    context_parts = []

    for index, result in enumerate(results, start=1):
        chunk = result["chunk"]

        title = chunk["metadata"]["title"]
        source = chunk["metadata"]["source"]
        text = chunk["text"]

        context_part = (
            f"[资料{index}]\n"
            f"标题：{title}\n"
            f"来源：{source}\n"
            f"内容：{text}"
        )

        context_parts.append(context_part)

    return "\n\n".join(context_parts)


if __name__ == "__main__":
    from agent.rag.reranker import retrieve_with_rerank

    results = retrieve_with_rerank(
        query="干宸浩有什么技术特点？",
        top_k=2,
        candidate_k=10,
        filters={"player": "干宸浩"}
    )

    context = build_context(results)

    print(context)