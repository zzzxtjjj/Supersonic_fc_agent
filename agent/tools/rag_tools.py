from agent.rag.reranker import retrieve_with_rerank


def search_team_knowledge(
    query: str,
    player: str | None = None,
    season: str | None = None,
    knowledge_type: str | None = None,
    top_k: int = 3
) -> dict:

    filters = {}

    # 1. 根据可选参数构造 metadata filters
    if player is not None:
        filters["player"] = player

    if season is not None:
        filters["season"] = season

    if knowledge_type is not None:
        filters["type"] = knowledge_type
    elif "战术" in query:
        filters["type"] = "tactics"

    # 2. 真正执行 Hybrid + Reranker
    results = retrieve_with_rerank(
        query=query,
        top_k=top_k,
        candidate_k=10,
        filters=filters if filters else None
    )

    # 3. 如果没搜到
    if not results:
        return {
            "success": False,
            "query": query,
            "filters": filters,
            "results": []
        }

    # 4. 把 Retriever 内部复杂结果整理成给 Agent 好读的结构
    knowledge = []

    for result in results:
        chunk = result["chunk"]

        knowledge.append(
            {
                "id": chunk["id"],
                "title": chunk["metadata"]["title"],
                "text": chunk["text"],
                "source": chunk["metadata"]["source"],
                "rerank_score": result["rerank_score"]
            }
        )

    return {
        "success": True,
        "query": query,
        "filters": filters,
        "results": knowledge
    }


SEARCH_TEAM_KNOWLEDGE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_team_knowledge",
        "description": (
            "搜索超音速足球队的非结构化知识。"
            "适用于球员技术特点、比赛风格、球队角色、球员故事、"
            "球队战术、比赛分析、赛季总结、球队文化和球队历史。"
            "用户指定赛季时必须原样传入season；该赛季无结果时应直接回答暂无数据，"
            "不得省略或替换season重新搜索。"
            "球衣号码、进球数、射手榜排名、比赛比分等精确结构化事实，"
            "应优先使用对应的专用结构化工具。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "需要从球队知识库检索的问题。"
                },
                "player": {
                    "type": "string",
                    "description": "可选，明确涉及某名球员时填写中文姓名。"
                },
                "season": {
                    "type": "string",
                    "description": "可选，明确限定某赛季时填写，例如25-26。"
                },
                "knowledge_type": {
                    "type": "string",
                    "description": (
                        "可选知识类型，例如player、tactics、match_analysis、"
                        "season_summary、team_culture、team_history。"
                    )
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回的知识块数量，默认3。"
                }
            },
            "required": ["query"]
        }
    }
}


if __name__ == "__main__":
    result = search_team_knowledge(
        query="干宸浩有什么技术特点？",
        player="干宸浩",
        top_k=2
    )

    print(result)
