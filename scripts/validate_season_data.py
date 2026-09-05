import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.season_data import (
    calculate_player_goal_totals,
    calculate_scorer_ranking,
    load_matches,
    load_players,
    load_season_file,
    load_standings,
    load_teams,
    supersonic_goals_for,
)


class SeasonValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationSummary:
    season: str
    team_count: int
    player_count: int
    match_count: int
    regular_match_count: int
    playoff_match_count: int
    regular_supersonic_goals: int
    standing_count: int


def _duplicates(values: list[object]) -> set[object]:
    seen: set[object] = set()
    duplicates: set[object] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def validate_season(season: str) -> ValidationSummary:
    season_info = load_season_file(season, "season.json")
    teams = load_teams(season)
    players = load_players(season)
    matches = load_matches(season)
    standings = load_standings(season)
    errors: list[str] = []

    if season_info.get("id") != season:
        errors.append("season.json id 与目录赛季不一致")

    team_ids = [team.get("id") for team in teams]
    player_ids = [player.get("id") for player in players]
    match_ids = [match.get("id") for match in matches]
    standing_ranks = [row.get("rank") for row in standings]

    for label, duplicates in (
        ("team_id", _duplicates(team_ids)),
        ("player_id", _duplicates(player_ids)),
        ("match id", _duplicates(match_ids)),
        ("standings rank", _duplicates(standing_ranks)),
    ):
        if duplicates:
            errors.append(f"{label} 重复：{sorted(duplicates)}")

    team_id_set = set(team_ids)
    player_id_set = set(player_ids)

    for match in matches:
        match_id = match.get("id", "<missing>")
        if match.get("season") != season:
            errors.append(f"{match_id}: season 与目录不一致")

        for key in ("home_team_id", "away_team_id"):
            if match.get(key) not in team_id_set:
                errors.append(f"{match_id}: {key} 不存在：{match.get(key)}")

        try:
            expected_goals = supersonic_goals_for(match)
        except (KeyError, ValueError) as exc:
            errors.append(str(exc))
            continue

        event_goals = sum(event.get("goals", 0) for event in match.get("scorers", []))
        if event_goals != expected_goals:
            errors.append(
                f"{match_id}: 超音速进球事件 {event_goals} != 比分 {expected_goals}"
            )

        for event in match.get("scorers", []):
            if event.get("type") == "player":
                if event.get("player_id") not in player_id_set:
                    errors.append(
                        f"{match_id}: scorer player_id 不存在：{event.get('player_id')}"
                    )
            elif event.get("type") == "own_goal":
                if event.get("player_id") is not None:
                    errors.append(f"{match_id}: own_goal 不得绑定个人 player_id")
            else:
                errors.append(f"{match_id}: scorer type 非法：{event.get('type')}")

    for row in standings:
        if row.get("team_id") not in team_id_set:
            errors.append(f"standings team_id 不存在：{row.get('team_id')}")

    regular_matches = [match for match in matches if match.get("stage") == "regular"]
    playoff_matches = [
        match for match in matches if match.get("stage") == "playoff_semifinal"
    ]
    regular_goals = sum(supersonic_goals_for(match) for match in regular_matches)
    player_goal_totals = calculate_player_goal_totals(matches)
    own_goal_total = sum(
        event["goals"]
        for match in matches
        for event in match.get("scorers", [])
        if event.get("type") == "own_goal"
    )
    all_event_goals = sum(
        event["goals"] for match in matches for event in match.get("scorers", [])
    )
    if sum(player_goal_totals.values()) + own_goal_total != all_event_goals:
        errors.append("own_goal 与个人进球的分离计算不一致")

    default_ranking = calculate_scorer_ranking(matches, players)
    eligible_by_id = {
        player["id"]: player.get("season_data", {}).get(
            "scorer_table_eligible", True
        )
        for player in players
    }
    ineligible_in_ranking = [
        entry["player_id"]
        for entry in default_ranking
        if not eligible_by_id.get(entry["player_id"], True)
    ]
    if ineligible_in_ranking:
        errors.append(f"默认射手榜包含不符合资格球员：{ineligible_in_ranking}")

    if season == "25-26":
        expected_roster = {
            "李云帆", "何柏霖", "干宸浩", "张文泽", "陈卓", "王恩博",
            "王浩涛", "姚翰荣", "谭丁睿", "朱余韬", "胡昊明", "展俊杰",
            "潘瑞晨", "伍瑜航", "吴光耀", "欧阳慷", "张谢童甲", "袁翰涛",
        }
        actual_roster = {player.get("name") for player in players}
        if len(players) != 18 or actual_roster != expected_roster:
            errors.append(
                "25-26 球员名单应为已确认的 18 人，"
                f"实际 {len(players)} 人"
            )
        if len(regular_matches) != 7:
            errors.append(f"25-26 常规赛应为 7 场，实际 {len(regular_matches)} 场")
        if len(playoff_matches) != 2:
            errors.append(f"25-26 季后赛应为 2 场，实际 {len(playoff_matches)} 场")
        if regular_goals != 23:
            errors.append(f"25-26 常规赛超音速进球应为 23，实际 {regular_goals}")
        if not default_ranking or (
            default_ranking[0]["player_id"] != "gan-chenhao"
            or default_ranking[0]["goals"] != 6
        ):
            errors.append("25-26 默认射手榜第一应为干宸浩 6 球")

    if errors:
        raise SeasonValidationError("赛季数据验证失败：\n- " + "\n- ".join(errors))

    return ValidationSummary(
        season=season,
        team_count=len(teams),
        player_count=len(players),
        match_count=len(matches),
        regular_match_count=len(regular_matches),
        playoff_match_count=len(playoff_matches),
        regular_supersonic_goals=regular_goals,
        standing_count=len(standings),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="验证 Supersonic 赛季展示数据")
    parser.add_argument("--season", default="25-26")
    args = parser.parse_args()

    try:
        summary = validate_season(args.season)
    except (SeasonValidationError, FileNotFoundError, ValueError) as exc:
        print(exc)
        return 1

    print(f"PASS: {summary.season}")
    print(f"球队: {summary.team_count}")
    print(f"球员: {summary.player_count}")
    print(f"比赛: {summary.match_count}")
    print(f"常规赛: {summary.regular_match_count}")
    print(f"季后赛: {summary.playoff_match_count}")
    print(f"常规赛超音速进球: {summary.regular_supersonic_goals}")
    print(f"积分榜: {summary.standing_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
