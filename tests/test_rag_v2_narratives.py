import json
from pathlib import Path

import pytest

from agent.rag.bm25_retriever import bm25_search


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "rag" / "chunks.json"
INDEX_PATH = PROJECT_ROOT / "data" / "rag" / "dense_index.json"
SOURCES_PATH = PROJECT_ROOT / "data" / "sources" / "official_posts.json"
MATCHES_PATH = PROJECT_ROOT / "data" / "seasons" / "25-26" / "matches.json"

NARRATIVE_IDS = {
    "narrative_r4_turning_point_001",
    "narrative_r5_playoff_race_001",
    "narrative_r5_rain_match_story_001",
    "narrative_r6_playoff_clinch_001",
    "narrative_r6_comeback_story_001",
    "narrative_r6_player_milestones_001",
    "narrative_25_26_low_to_playoffs_001",
    "narrative_25_26_squad_transition_001",
}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("query", "expected_id"),
    [
        ("25-26第四轮4-0命运为什么是赛季转折点", "narrative_r4_turning_point_001"),
        ("第五轮对天行者为什么是争四关键战", "narrative_r5_playoff_race_001"),
        ("第六轮为什么提前锁定季后赛席位", "narrative_r6_playoff_clinch_001"),
        ("25-26赛季整体成绩和历史最佳战绩", "season_25_26_review_001"),
        ("25-26赛季球队如何更新换代", "narrative_25_26_squad_transition_001"),
        ("26-27赛季队长交接是谁", "culture_captain_succession_001"),
    ],
)
def test_high_value_narrative_is_retrievable(query: str, expected_id: str) -> None:
    ids = [result["chunk"]["id"] for result in bm25_search(query, top_k=3)]
    assert expected_id in ids


def test_new_narratives_have_valid_provenance_and_match_references() -> None:
    chunks = {chunk["id"]: chunk for chunk in _load(CHUNKS_PATH)}
    source_ids = {source["id"] for source in _load(SOURCES_PATH)["sources"]}
    match_ids = {match["id"] for match in _load(MATCHES_PATH)["matches"]}

    assert NARRATIVE_IDS <= chunks.keys()
    for chunk_id in NARRATIVE_IDS:
        chunk = chunks[chunk_id]
        metadata = chunk["metadata"]
        assert 80 <= len(chunk["text"]) <= 250
        assert metadata["season"] == "25-26"
        assert metadata["category"]
        assert metadata["source_id"] in source_ids
        assert set(metadata.get("source_ids", [])) <= source_ids
        if metadata["type"] == "match_analysis":
            assert metadata["match_id"] in match_ids


def test_narratives_do_not_reintroduce_false_r5_assist_or_duplicates() -> None:
    chunks = _load(CHUNKS_PATH)
    corpus = "\n".join(chunk["text"] for chunk in chunks)
    normalized = ["".join(chunk["text"].split()) for chunk in chunks]

    assert "张谢童甲第五轮后场断球后精准长传助攻破门" not in corpus
    assert "张谢童甲第五轮助攻破门" not in corpus
    assert len(normalized) == len(set(normalized))


def test_dense_index_matches_all_chunks_after_narrative_rebuild() -> None:
    chunks = _load(CHUNKS_PATH)
    index = _load(INDEX_PATH)

    assert len(chunks) == len(index)
    assert [chunk["id"] for chunk in chunks] == [item["id"] for item in index]
    assert {len(item["embedding"]) for item in index} == {512}
