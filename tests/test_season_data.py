from fastapi.testclient import TestClient

from backend.api.season_data import (
    calculate_player_goal_totals,
    calculate_scorer_ranking,
    load_matches,
    load_players,
    load_standings,
    load_teams,
    supersonic_goals_for,
)
from backend.main import app
from scripts.validate_season_data import validate_season


def test_25_26_match_counts_and_regular_goals() -> None:
    matches = load_matches("25-26")
    regular = [match for match in matches if match["stage"] == "regular"]
    playoffs = [
        match for match in matches if match["stage"] == "playoff_semifinal"
    ]

    assert len(regular) == 7
    assert len(playoffs) == 2
    assert len(matches) == 9
    assert sum(supersonic_goals_for(match) for match in regular) == 23


def test_scorer_totals_eligibility_and_own_goal() -> None:
    matches = load_matches("25-26")
    players = load_players("25-26")
    totals = calculate_player_goal_totals(matches)
    default_ranking = calculate_scorer_ranking(matches, players)
    all_scorers = calculate_scorer_ranking(
        matches,
        players,
        show_all_scorers=True,
    )
    default_by_id = {entry["player_id"]: entry for entry in default_ranking}
    all_by_id = {entry["player_id"]: entry for entry in all_scorers}

    assert totals["wu-guangyao"] == 6
    assert "wu-guangyao" not in default_by_id
    assert all_by_id["wu-guangyao"]["goals"] == 6
    assert default_by_id["gan-chenhao"]["goals"] == 6
    assert default_by_id["wang-enbo"]["goals"] == 3
    assert default_by_id["zhang-xietongjia"]["goals"] == 3
    assert "hu-haoming" not in totals

    own_goals = [
        event
        for match in matches
        for event in match["scorers"]
        if event["type"] == "own_goal"
    ]
    assert own_goals == [
        {"type": "own_goal", "goals": 1, "note": "胡昊明逼抢造成"}
    ]


def test_supersonic_standing_is_exact() -> None:
    standings = load_standings("25-26")
    supersonic = next(row for row in standings if row["team_id"] == "supersonic")

    assert len(standings) == 8
    assert supersonic == {
        "rank": 4,
        "team_id": "supersonic",
        "points": 12,
        "goal_difference": -2,
        "goals_for": 23,
    }


def test_team_aliases_and_media_contracts() -> None:
    teams = {team["id"]: team for team in load_teams("25-26")}
    players = load_players("25-26")

    assert "诺丁汉国际队" in teams["international"]["aliases"]
    assert "中桌 FC（圆桌骑士）" in teams["round-table-knights"]["aliases"]
    assert teams["supersonic"]["crest_url"] == "/supersonic-logo.png"
    assert all(
        team["crest_url"] is None or team["crest_url"].startswith("/media/team/")
        for team_id, team in teams.items()
        if team_id != "supersonic"
    )
    assert all("photo_url" in player for player in players)


def test_25_26_roster_contains_all_18_confirmed_players() -> None:
    players = load_players("25-26")

    assert len(players) == 18
    assert [player["name"] for player in players] == [
        "李云帆", "何柏霖", "干宸浩", "张文泽", "陈卓", "王恩博",
        "王浩涛", "姚翰荣", "谭丁睿", "朱余韬", "胡昊明", "展俊杰",
        "潘瑞晨", "伍瑜航", "吴光耀", "欧阳慷", "张谢童甲", "袁翰涛",
    ]
    assert all(
        player["photo_url"] is None
        or player["photo_url"].startswith("/media/player/")
        for player in players
    )
    assert next(player for player in players if player["name"] == "李云帆")[
        "season_data"
    ]["is_captain"] is True
    assert next(player for player in players if player["name"] == "姚翰荣")[
        "season_data"
    ]["is_captain"] is True


def test_confirmed_dominant_foot_values_are_consistent_across_seasons() -> None:
    no_weak_foot_players = {"干宸浩", "张谢童甲"}

    for season in ("25-26", "26-27"):
        for player in load_players(season):
            expected = (
                "左右脚均衡（无逆足）"
                if player["name"] in no_weak_foot_players
                else "右脚"
            )
            assert player["dominant_foot"] == expected


def test_season_validator_accepts_complete_and_empty_seasons() -> None:
    complete = validate_season("25-26")
    empty = validate_season("26-27")

    assert complete.match_count == 9
    assert complete.regular_supersonic_goals == 23
    assert empty.match_count == 0
    assert empty.standing_count == 0


def test_backend_season_endpoints() -> None:
    client = TestClient(app)

    matches_response = client.get("/api/matches", params={"season": "25-26"})
    standings_response = client.get(
        "/api/stats/standings", params={"season": "25-26"}
    )
    scorers_response = client.get(
        "/api/stats/scorers", params={"season": "25-26"}
    )
    all_scorers_response = client.get(
        "/api/stats/scorers",
        params={"season": "25-26", "show_all_scorers": "true"},
    )
    players_response = client.get("/api/players", params={"season": "25-26"})

    assert matches_response.status_code == 200
    assert matches_response.json()["total"] == 9
    assert standings_response.status_code == 200
    assert len(standings_response.json()["items"]) == 8
    assert scorers_response.json()["items"][0]["player_name"] == "干宸浩"
    assert "吴光耀" not in {
        item["player_name"] for item in scorers_response.json()["items"]
    }
    assert "吴光耀" in {
        item["player_name"] for item in all_scorers_response.json()["items"]
    }
    assert players_response.status_code == 200
    assert players_response.json()["total"] == 18


def test_26_27_api_returns_only_confirmed_roster_and_no_match_stats() -> None:
    client = TestClient(app)

    assert client.get("/api/matches", params={"season": "26-27"}).json()[
        "items"
    ] == []
    assert client.get(
        "/api/stats/standings", params={"season": "26-27"}
    ).json()["items"] == []
    assert client.get(
        "/api/stats/scorers", params={"season": "26-27"}
    ).json()["items"] == []
    players = client.get("/api/players", params={"season": "26-27"}).json()
    assert players["total"] == 12
    names = {item["player"]["name"] for item in players["items"]}
    assert "吴光耀" not in names
    assert names.isdisjoint({"李云帆", "张文泽", "王浩涛", "姚翰荣", "伍瑜航"})
    captains = {
        item["player"]["name"]
        for item in players["items"]
        if item["season"]["is_captain"]
    }
    assert captains == {"干宸浩", "张谢童甲"}
