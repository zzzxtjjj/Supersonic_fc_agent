PLAYERS = {
    "张谢童甲": {
        "position": "右前卫/后腰",

        "numbers": {
            "25-26": 39
        },

        "goals": {
            "25-26": 3
        }
    },

    "干宸浩": {
        "position": "左前卫",

        "numbers": {
            "25-26": 6
        },

        "goals": {
            "25-26": 6
        }
    }
}


def get_player_profile(name: str) -> dict:
    """
    查询某名球员的基础资料。
    """

    if name not in PLAYERS:
        return {
            "success": False,
            "error": "player_not_found"
        }

    player_data = PLAYERS[name]

    return {
        "success": True,
        "name": name,
        "position": player_data["position"]
    }


def get_player_number(name: str, season: str) -> dict:
    """
    查询某名球员在指定赛季的球衣号码。
    """

    if name not in PLAYERS:
        return {
            "success": False,
            "error": "player_not_found"
        }

    numbers_data = PLAYERS[name]["numbers"]

    if season not in numbers_data:
        return {
            "success": False,
            "error": "season_not_found"
        }

    return {
        "success": True,
        "name": name,
        "season": season,
        "number": numbers_data[season]
    }
    


def get_player_goals(name: str, season: str) -> dict:
    """
    查询某名球员某个赛季的进球数。
    """

    if name not in PLAYERS:
        return {
            "success": False,
            "error": "player_not_found"
        }

    goals_data = PLAYERS[name]["goals"]

    if season not in goals_data:
        return {
            "success": False,
            "error": "season_not_found"
        }

    return {
        "success": True,
        "name": name,
        "season": season,
        "goals": goals_data[season]
    }


def get_scorer_ranking(season: str) -> dict:
    ranking_data = []

    for player in PLAYERS:
        goals_data = PLAYERS[player]["goals"]

        if season not in goals_data:
            continue

        ranking_data.append(
            {
                "name": player,
                "goals": goals_data[season],
            }
        )

    ranking_data.sort(
        key=lambda player: player["goals"],
        reverse=True
    )

    previous_goals = None
    current_rank = 0

    for index, player in enumerate(ranking_data, start=1):

        if player["goals"] != previous_goals:
            current_rank = index

        player["rank"] = current_rank

        previous_goals = player["goals"]

    return {
        "success": True,
        "season": season,
        "ranking": ranking_data
    }


GET_PLAYER_GOALS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_player_goals",
        "description": "查询超音速足球队某名球员在指定赛季的进球数。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "球员姓名，例如张谢童甲"
                },
                "season": {
                    "type": "string",
                    "description": "赛季，例如25-26"
                }
            },
            "required": [
                "name",
                "season"
            ]
        }
    }
}


GET_PLAYER_PROFILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_player_profile",
        "description": "查询超音速足球队某名球员的基础资料，包括球衣号码和场上位置。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "球员姓名，例如张谢童甲"
                }
            },
            "required": [
                "name"
            ]
        }
    }
}


GET_PLAYER_NUMBER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_player_number",
        "description": "查询超音速足球队某名球员在指定赛季的球衣号码。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "球员姓名，例如张谢童甲"
                },
                "season": {
                    "type": "string",
                    "description": "赛季，例如25-26"
                }
            },
            "required": ["name", "season"]
        }
    }
}


GET_SCORER_RANKING_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_scorer_ranking",
        "description": (
            "查询超音速足球队指定赛季的完整射手榜、进球排名、射手榜第一、前几名、"
            "某球员在射手榜中的排名。遇到'射手榜'、'排名'、'第一是谁'、'前几名'等问题时应优先调用此工具。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "season": {
                    "type": "string",
                    "description": "赛季，例如25-26"
                }
            },
            "required": ["season"]
        }
    }
}
