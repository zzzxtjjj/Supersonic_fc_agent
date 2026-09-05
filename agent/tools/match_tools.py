MATCHES = {
    "25-26": {
        "示例对手A": {
            "score": "2-1",
            "scorers": ["张谢童甲", "干宸浩"]
        },
        "示例对手B": {
            "score": "1-1",
            "scorers": ["干宸浩"]
        }
    }
}


def get_match_result(season: str, opponent: str) -> dict:
    """
    查询指定赛季对阵某个对手的比赛结果。
    """

    if season not in MATCHES:
        return {
            "success": False,
            "error": "season_not_found"
        }

    season_matches = MATCHES[season]

    if opponent not in season_matches:
        return {
            "success": False,
            "error": "match_not_found"
        }

    match_data = season_matches[opponent]

    return {
        "success": True,
        "season": season,
        "opponent": opponent,
        "score": match_data["score"],
        "scorers": match_data["scorers"]
    }


GET_MATCH_RESULT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_match_result",
        "description": "查询超音速足球队在指定赛季对阵某个对手的比赛结果，包括比分和进球球员。",
        "parameters": {
            "type": "object",
            "properties": {
                "season": {
                    "type": "string",
                    "description": "赛季，例如25-26"
                },
                "opponent": {
                    "type": "string",
                    "description": "对手球队名称"
                }
            },
            "required": ["season", "opponent"]
        }
    }
}