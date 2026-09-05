from agent.tools.player_tools import (
    get_player_goals,
    get_player_number,
    get_player_profile,
    get_scorer_ranking,
)


def test_confirmed_player_profile_and_goals() -> None:
    assert get_player_profile("张谢童甲") == {
        "success": True,
        "name": "张谢童甲",
        "position": "右前卫 / 后腰",
    }
    assert get_player_goals("干宸浩", "25-26") == {
        "success": True,
        "name": "干宸浩",
        "season": "25-26",
        "goals": 6,
    }


def test_unknown_player_and_season_fail_safely() -> None:
    assert get_player_profile("梅西") == {
        "success": False,
        "error": "player_not_found",
    }
    assert get_player_goals("张谢童甲", "24-25") == {
        "success": False,
        "error": "season_not_found",
    }


def test_tools_read_players_outside_the_old_two_player_fixture() -> None:
    assert get_player_number("李云帆", "25-26") == {
        "success": True,
        "name": "李云帆",
        "season": "25-26",
        "number": 1,
    }
    assert get_player_goals("李云帆", "25-26") == {
        "success": True,
        "name": "李云帆",
        "season": "25-26",
        "goals": 0,
    }


def test_scorer_ranking_uses_the_complete_season_match_data() -> None:
    result = get_scorer_ranking("25-26")

    assert result["success"] is True
    assert result["season"] == "25-26"
    assert result["ranking"] == [
        {"name": "干宸浩", "goals": 6, "rank": 1},
        {"name": "王恩博", "goals": 3, "rank": 2},
        {"name": "张谢童甲", "goals": 3, "rank": 2},
        {"name": "陈卓", "goals": 1, "rank": 4},
        {"name": "谭丁睿", "goals": 1, "rank": 4},
        {"name": "姚翰荣", "goals": 1, "rank": 4},
        {"name": "袁翰涛", "goals": 1, "rank": 4},
        {"name": "朱余韬", "goals": 1, "rank": 4},
    ]


def test_scorer_ranking_does_not_turn_missing_season_data_into_an_empty_table() -> None:
    assert get_scorer_ranking("26-27") == {
        "success": False,
        "error": "season_not_found",
    }
