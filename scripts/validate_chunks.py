import json
import sys
from collections import Counter
from pathlib import Path


CHUNKS_PATH = Path(__file__).resolve().parents[1] / "data" / "rag" / "chunks.json"
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
REQUIRED_METADATA = {
    "source",
    "title",
    "type",
    "topic",
    "player",
    "season",
    "status",
    "keywords",
}


def main() -> int:
    errors = []

    try:
        chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
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

    if duplicate_ids:
        errors.append(f"dataset: {duplicate_ids} duplicate id(s)")

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
