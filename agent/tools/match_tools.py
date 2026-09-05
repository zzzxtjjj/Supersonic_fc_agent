from backend.api.season_data import (
    SUPERSONIC_TEAM_ID,
    SeasonDataNotFound,
    load_matches,
    load_teams,
)


def _normalize_team_name(value: str) -> str:
    return "".join(value.lower().split())


def _opponent_team_id(season: str, opponent: str) -> str | None:
    target = _normalize_team_name(opponent)
    for team in load_teams(season):
        names = [team.get("name", ""), *team.get("aliases", [])]
        if any(_normalize_team_name(name) == target for name in names):
            return team["id"]
    return None


def _supersonic_score(match: dict) -> tuple[int, int]:
    if match["home_team_id"] == SUPERSONIC_TEAM_ID:
        return match["home_score"], match["away_score"]
    return match["away_score"], match["home_score"]


def get_match_result(
    season: str,
    opponent: str,
    round: int | None = None,
    stage: str | None = None,
    leg: int | None = None,
) -> dict:
    """从正式赛季数据查询一场可唯一确定的比赛结果。"""

    try:
        opponent_id = _opponent_team_id(season, opponent)
        matches = load_matches(season)
    except SeasonDataNotFound:
        return {"success": False, "error": "season_not_found"}

    if opponent_id is None or opponent_id == SUPERSONIC_TEAM_ID:
        return {"success": False, "error": "match_not_found"}

    candidates = [
        match
        for match in matches
        if opponent_id in {match["home_team_id"], match["away_team_id"]}
        and SUPERSONIC_TEAM_ID in {match["home_team_id"], match["away_team_id"]}
        and (round is None or match.get("round") == round)
        and (stage is None or match.get("stage") == stage)
        and (leg is None or match.get("leg") == leg)
    ]

    if not candidates:
        return {"success": False, "error": "match_not_found"}
    if len(candidates) > 1:
        return {
            "success": False,
            "error": "multiple_matches_found",
            "match_ids": [match["id"] for match in candidates],
        }

    match = candidates[0]
    goals_for, goals_against = _supersonic_score(match)
    scorers = []
    for scorer in match.get("scorers", []):
        if scorer.get("type") == "own_goal":
            scorers.append("对手乌龙")
            continue
        player_name = scorer.get("player_name")
        goals = scorer.get("goals", 0)
        if player_name:
            scorers.append(f"{player_name} x{goals}" if goals > 1 else player_name)

    return {
        "success": True,
        "season": season,
        "opponent": opponent,
        "match_id": match["id"],
        "score": f"{goals_for}-{goals_against}",
        "scorers": scorers,
    }


GET_MATCH_RESULT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_match_result",
        "description": (
            "查询超音速足球队在指定赛季对阵某个对手的比赛结果，包括比分和进球球员。"
            "若同一对手有多场比赛，请提供轮次、阶段或回合以唯一确定比赛。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "season": {
                    "type": "string",
                    "description": "赛季，例如25-26",
                },
                "opponent": {
                    "type": "string",
                    "description": "对手球队名称或现有别名",
                },
                "round": {
                    "type": "integer",
                    "description": "可选的常规赛轮次",
                },
                "stage": {
                    "type": "string",
                    "description": "可选阶段，例如regular或playoff_semifinal",
                },
                "leg": {
                    "type": "integer",
                    "description": "可选的季后赛回合",
                },
            },
            "required": ["season", "opponent"],
        },
    },
}
