import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHUNKS_PATH = PROJECT_ROOT / "data" / "rag" / "chunks.json"
DENSE_INDEX_PATH = PROJECT_ROOT / "data" / "rag" / "dense_index.json"


def load_chunks() -> list[dict]:
    with open(CHUNKS_PATH, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    return chunks


def load_dense_index() -> list[dict]:
    with open(DENSE_INDEX_PATH, "r", encoding="utf-8") as file:
        index = json.load(file)

    return index