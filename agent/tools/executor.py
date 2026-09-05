import json

from agent.tools.player_tools import (
    get_player_goals,
    get_player_profile,
    get_player_number,
    get_scorer_ranking,
    GET_PLAYER_GOALS_SCHEMA,
    GET_PLAYER_PROFILE_SCHEMA,
    GET_PLAYER_NUMBER_SCHEMA,
    GET_SCORER_RANKING_SCHEMA,
)

from agent.tools.match_tools import (
    get_match_result,
    GET_MATCH_RESULT_SCHEMA,
)

from agent.tools.rag_tools import (
    search_team_knowledge,
    SEARCH_TEAM_KNOWLEDGE_SCHEMA,
)

TOOL_REGISTRY = {
    "get_player_goals": get_player_goals,
    "get_player_profile": get_player_profile,
    "get_player_number": get_player_number,
    "get_scorer_ranking": get_scorer_ranking,
    "get_match_result": get_match_result,
    "search_team_knowledge": search_team_knowledge
}

TOOL_SCHEMAS = [
    GET_PLAYER_GOALS_SCHEMA,
    GET_PLAYER_PROFILE_SCHEMA,
    GET_PLAYER_NUMBER_SCHEMA,
    GET_SCORER_RANKING_SCHEMA,
    GET_MATCH_RESULT_SCHEMA,
    SEARCH_TEAM_KNOWLEDGE_SCHEMA
]

from agent.tools.rag_tools import (
    search_team_knowledge,
    SEARCH_TEAM_KNOWLEDGE_SCHEMA
)


def execute_tool(tool_name: str, arguments: str) -> dict:
    """
    根据工具名称和参数执行对应的 Python 函数。
    """

    if tool_name not in TOOL_REGISTRY:
        return {
            "success": False,
            "error": "tool_not_found"
        }

    tool_function = TOOL_REGISTRY[tool_name]

    parsed_arguments = json.loads(arguments)

    result = tool_function(**parsed_arguments)

    return result