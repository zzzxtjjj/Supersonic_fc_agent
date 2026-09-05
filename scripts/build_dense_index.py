from agent.rag.loader import load_chunks
from agent.rag.embedder import embed_text
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INDEX_PATH = PROJECT_ROOT / "data" / "rag" / "dense_index.json"

# 提前把知识块全部转换成向量，并保存下来，避免每次用户提问都重新算一遍。
def build_dense_index() -> list[dict]:
    chunks = load_chunks()

    index = []

    for chunk in chunks:
        text = chunk["text"]

        # 1. 给当前 chunk 生成 embedding
        embedding = embed_text(text)

        # 2. 创建一条索引记录
        index_item = {
            "id": chunk["id"],
            "text": text,
            "metadata": chunk["metadata"],
            "embedding": embedding
        }

        # 3. 加入整个 index
        index.append(index_item)

    return index



def save_dense_index(index: list[dict]) -> None:
    with open(INDEX_PATH, "w", encoding="utf-8") as file:
        json.dump(
            index,
            file,
            ensure_ascii=False,
            indent=2
        )


def main() -> int:
    index = build_dense_index()
    save_dense_index(index)
    embedding_dimension = len(index[0]["embedding"]) if index else 0
    print(f"Dense index rebuilt: {len(index)} chunks, dimension {embedding_dimension}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
