from backend.api.season_data import (
    SEASON_DATA_ROOT,
    SeasonDataNotFound,
    calculate_player_goal_totals,
    calculate_scorer_ranking,
    load_matches,
    load_players,
)


def _available_seasons() -> list[str]:
    return [
        path.name
        for path in sorted(SEASON_DATA_ROOT.iterdir(), reverse=True)
        if path.is_dir() and (path / "players.json").is_file()
    ]


def _find_player(players: list[dict], name: str) -> dict | None:
    return next((player for player in players if player.get("name") == name), None)


def _player_exists(name: str) -> bool:
    for season in _available_seasons():
        try:
            if _find_player(load_players(season), name) is not None:
                return True
        except SeasonDataNotFound:
            continue
    return False


def get_player_profile(name: str) -> dict:
    """查询某名球员最新的已确认基础资料。"""

    player_found = False
    for season in _available_seasons():
        try:
            player = _find_player(load_players(season), name)
        except SeasonDataNotFound:
            continue
        if player is not None:
            player_found = True
            position = player.get("season_data", {}).get("position")
            if position is not None:
                return {
                    "success": True,
                    "name": name,
                    "position": position,
                }

    if player_found:
        return {
            "success": True,
            "name": name,
            "position": None,
        }

    return {
        "success": False,
        "error": "player_not_found",
    }


def get_player_number(name: str, season: str) -> dict:
    """查询某名球员在指定赛季的球衣号码。"""

    try:
        player = _find_player(load_players(season), name)
    except SeasonDataNotFound:
        return {
            "success": False,
            "error": "season_not_found",
        }

    if player is None:
        return {
            "success": False,
            "error": "season_not_found" if _player_exists(name) else "player_not_found",
        }

    number = player.get("season_data", {}).get("number")
    if number is None:
        return {
            "success": False,
            "error": "season_not_found",
        }

    return {
        "success": True,
        "name": name,
        "season": season,
        "number": number,
    }


def get_player_goals(name: str, season: str) -> dict:
    """查询某名球员在指定赛季已记录比赛中的进球数。"""

    try:
        players = load_players(season)
        matches = load_matches(season)
    except SeasonDataNotFound:
        return {
            "success": False,
            "error": "season_not_found",
        }

    player = _find_player(players, name)
    if player is None:
        return {
            "success": False,
            "error": "season_not_found" if _player_exists(name) else "player_not_found",
        }

    if not matches:
        return {
            "success": False,
            "error": "season_not_found",
        }

    goals = calculate_player_goal_totals(matches).get(player["id"], 0)

    return {
        "success": True,
        "name": name,
        "season": season,
        "goals": goals,
    }


def get_scorer_ranking(season: str) -> dict:
    """查询指定赛季由正式比赛记录计算的队内射手榜。"""

    try:
        players = load_players(season)
        matches = load_matches(season)
    except SeasonDataNotFound:
        return {
            "success": False,
            "error": "season_not_found",
        }

    if not matches:
        return {
            "success": False,
            "error": "season_not_found",
        }

    ranking_data = [
        {
            "name": entry["player_name"],
            "goals": entry["goals"],
            "rank": entry["rank"],
        }
        for entry in calculate_scorer_ranking(matches, players)
    ]

    return {
        "success": True,
        "season": season,
        "ranking": ranking_data,
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
                    "description": "球员姓名，例如张谢童甲",
                },
                "season": {
                    "type": "string",
                    "description": "赛季，例如25-26",
                },
            },
            "required": ["name", "season"],
        },
    },
}


GET_PLAYER_PROFILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_player_profile",
        "description": "查询超音速足球队某名球员最新的已确认基础资料和场上位置。",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "球员姓名，例如张谢童甲",
                },
            },
            "required": ["name"],
        },
    },
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
                    "description": "球员姓名，例如张谢童甲",
                },
                "season": {
                    "type": "string",
                    "description": "赛季，例如25-26",
                },
            },
            "required": ["name", "season"],
        },
    },
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
                    "description": "赛季，例如25-26",
                },
            },
            "required": ["season"],
        },
    },
}
