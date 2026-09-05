# 接收用户问题，完成检索、重排、构建 context，然后调用 LLM 基于资料回答。
from agent.llm.openrouter_client import call_llm
from agent.rag.reranker import retrieve_with_rerank
from agent.rag.context_builder import build_context


def rag_answer(
    query: str,
    filters: dict | None = None,
    top_k: int = 3
) -> str:

    results = retrieve_with_rerank(query, top_k, filters=filters)

    if not results:
        return "暂无相关知识。"

    context = build_context(results)

    messages = [
        {
            "role": "system",
            "content": (
                "你是超音速足球队知识助手。"
                "回答时必须严格依据提供的资料。"
                "不要补充资料中没有明确支持的事实。"
                "如果资料不足，请明确说暂无相关信息。"
            )
        },
        {
            "role": "user",
            "content": f"""
用户问题：
{query}

检索资料：
{context}

请仅根据以上资料回答用户问题。
"""
        }
    ]

    response = call_llm(messages=messages)

    return response["choices"][0]["message"]["content"]


if __name__ == "__main__":
    answer = rag_answer(
        query="干宸浩有什么技术特点？",
        filters={"player": "干宸浩"},
        top_k=2
    )

    print(answer)