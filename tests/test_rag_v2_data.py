import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "rag" / "chunks.json"
INDEX_PATH = PROJECT_ROOT / "data" / "rag" / "dense_index.json"
SOURCES_PATH = PROJECT_ROOT / "data" / "sources" / "official_posts.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_v2_rag_provenance_and_match_ids_are_valid() -> None:
    chunks = _load(CHUNKS_PATH)
    source_ids = {source["id"] for source in _load(SOURCES_PATH)["sources"]}

    for chunk in chunks:
        metadata = chunk["metadata"]
        assert "season" in metadata
        assert "source_id" in metadata
        assert isinstance(metadata["category"], str)
        assert metadata["category"]
        assert metadata["source_id"] is None or metadata["source_id"] in source_ids
        if "source_ids" in metadata:
            assert set(metadata["source_ids"]) <= source_ids
        if metadata["type"] == "match_analysis":
            assert metadata["match_id"]


def test_v2_rag_has_no_duplicate_or_reintroduced_false_fact() -> None:
    chunks = _load(CHUNKS_PATH)
    normalized = ["".join(chunk["text"].split()) for chunk in chunks]
    corpus = "\n".join(chunk["text"] for chunk in chunks)

    assert len(normalized) == len(set(normalized))
    assert "张谢童甲第五轮后场断球后精准长传助攻破门" not in corpus
    assert "王恩博在第六轮直塞助攻干宸浩" not in corpus
    assert "第六轮干宸浩助攻王恩博" in corpus
    assert "不能据此生成官方完整助攻榜" in corpus


def test_dense_index_is_synchronized_with_v2_chunks() -> None:
    chunks = _load(CHUNKS_PATH)
    index = _load(INDEX_PATH)

    assert len(index) == len(chunks)
    assert [item["id"] for item in index] == [chunk["id"] for chunk in chunks]
    assert [item["text"] for item in index] == [chunk["text"] for chunk in chunks]
    assert [item["metadata"] for item in index] == [
        chunk["metadata"] for chunk in chunks
    ]
    dimensions = {len(item["embedding"]) for item in index}
    assert dimensions == {512}
