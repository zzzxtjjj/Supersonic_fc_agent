from agent.tools.match_tools import get_match_result


def test_match_tool_reads_real_season_data_and_aliases() -> None:
    assert get_match_result("25-26", "命运队") == {
        "success": True,
        "season": "25-26",
        "opponent": "命运队",
        "match_id": "25-26-regular-04",
        "score": "4-0",
        "scorers": ["王恩博", "对手乌龙", "张谢童甲", "干宸浩"],
    }
    assert get_match_result("25-26", "中桌 FC") == {
        "success": True,
        "season": "25-26",
        "opponent": "中桌 FC",
        "match_id": "25-26-regular-06",
        "score": "5-2",
        "scorers": ["王恩博", "干宸浩 x2", "朱余韬", "姚翰荣"],
    }


def test_match_tool_requires_disambiguation_for_repeated_opponent() -> None:
    result = get_match_result("25-26", "年轻人")

    assert result["success"] is False
    assert result["error"] == "multiple_matches_found"
    assert len(result["match_ids"]) == 3
    assert get_match_result("25-26", "年轻人", round=3)["score"] == "0-9"
    assert get_match_result(
        "25-26", "年轻人", stage="playoff_semifinal", leg=2
    )["score"] == "1-3"


def test_match_tool_unknown_values_fail_safely() -> None:
    assert get_match_result("24-25", "命运") == {
        "success": False,
        "error": "season_not_found",
    }
    assert get_match_result("25-26", "不存在球队") == {
        "success": False,
        "error": "match_not_found",
    }
