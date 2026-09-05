import json
import sys
from collections import Counter
from pathlib import Path


CHUNKS_PATH = Path(__file__).resolve().parents[1] / "data" / "rag" / "chunks.json"
SOURCES_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "sources" / "official_posts.json"
)
ALLOWED_SEASONS = {"25-26", "26-27"}
CONFIRMED_26_27_FACT = "26-27赛季，干宸浩和张谢童甲担任超音速球队队长。"
ALLOWED_TYPES = {
    "player",
    "tactics",
    "match_analysis",
    "season_summary",
    "team_culture",
    "team_history",
}
ALLOWED_CATEGORIES = ALLOWED_TYPES | {
    "season_turning_point",
    "match_context",
    "match_story",
    "playoff_clinch",
    "player_milestone",
    "season_story",
    "squad_transition",
    "graduation_transition",
    "captain_transition",
    "season_identity",
}
REQUIRED_METADATA = {
    "source",
    "title",
    "type",
    "topic",
    "player",
    "season",
    "status",
    "keywords",
    "source_id",
    "category",
}


def main() -> int:
    errors = []

    try:
        chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
        source_payload = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Validation failed: {exc}")
        return 1

    if not isinstance(chunks, list):
        print("Validation failed: top-level JSON value must be a list")
        return 1

    ids = [
        chunk.get("id")
        for chunk in chunks
        if isinstance(chunk, dict) and isinstance(chunk.get("id"), str)
    ]
    duplicate_ids = sum(count - 1 for count in Counter(ids).values() if count > 1)
    sources = source_payload.get("sources", [])
    source_ids = [source.get("id") for source in sources]
    source_id_set = set(source_ids)
    if len(source_ids) != len(source_id_set):
        errors.append("sources: duplicate source id")

    normalized_texts = [
        "".join(chunk.get("text", "").split())
        for chunk in chunks
        if isinstance(chunk, dict) and isinstance(chunk.get("text"), str)
    ]
    duplicate_texts = sum(
        count - 1 for count in Counter(normalized_texts).values() if count > 1
    )

    for index, chunk in enumerate(chunks):
        label = f"chunk[{index}]"
        if not isinstance(chunk, dict):
            errors.append(f"{label}: must be an object")
            continue
        if not isinstance(chunk.get("id"), str) or not chunk["id"].strip():
            errors.append(f"{label}: id must be a non-empty string")
        if not isinstance(chunk.get("text"), str) or not chunk["text"].strip():
            errors.append(f"{label}: text must be a non-empty string")
        metadata = chunk.get("metadata")
        if not isinstance(metadata, dict):
            errors.append(f"{label}: metadata must be an object")
            continue
        missing = REQUIRED_METADATA - metadata.keys()
        if missing:
            errors.append(f"{label}: missing metadata fields {sorted(missing)}")
        if metadata.get("type") not in ALLOWED_TYPES:
            errors.append(f"{label}: unsupported type {metadata.get('type')!r}")
        if not isinstance(metadata.get("keywords"), list):
            errors.append(f"{label}: keywords must be a list")
        if metadata.get("season") not in ALLOWED_SEASONS:
            errors.append(f"{label}: unsupported season {metadata.get('season')!r}")
        if metadata.get("category") not in ALLOWED_CATEGORIES:
            errors.append(
                f"{label}: unsupported category {metadata.get('category')!r}"
            )

        source_id = metadata.get("source_id")
        if source_id is not None and source_id not in source_id_set:
            errors.append(f"{label}: unknown source_id {source_id!r}")

        chunk_source_ids = metadata.get("source_ids")
        if chunk_source_ids is not None:
            if not isinstance(chunk_source_ids, list):
                errors.append(f"{label}: source_ids must be a list")
            else:
                invalid_source_ids = sorted(set(chunk_source_ids) - source_id_set)
                if invalid_source_ids:
                    errors.append(
                        f"{label}: unknown source_ids {invalid_source_ids!r}"
                    )

        if metadata.get("type") == "match_analysis":
            match_id = metadata.get("match_id")
            if not isinstance(match_id, str) or not match_id:
                errors.append(f"{label}: match chunk must include match_id")

    if duplicate_ids:
        errors.append(f"dataset: {duplicate_ids} duplicate id(s)")
    if duplicate_texts:
        errors.append(f"dataset: {duplicate_texts} duplicate normalized text(s)")

    season_26_27 = [
        chunk
        for chunk in chunks
        if isinstance(chunk, dict)
        and isinstance(chunk.get("metadata"), dict)
        and chunk["metadata"].get("season") == "26-27"
    ]
    if len(season_26_27) != 1:
        errors.append(
            f"dataset: expected exactly one 26-27 chunk, found {len(season_26_27)}"
        )
    elif season_26_27[0].get("text") != CONFIRMED_26_27_FACT:
        errors.append("dataset: 26-27 chunk contains unconfirmed information")

    if errors:
        print("Validation failed")
        print(f"Total chunks: {len(chunks)}")
        print(f"Duplicate IDs: {duplicate_ids}")
        print(f"Invalid chunks: {len(errors)}")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed")
    print(f"Total chunks: {len(chunks)}")
    print(f"Duplicate IDs: {duplicate_ids}")
    print("Invalid chunks: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
