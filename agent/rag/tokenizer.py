_jieba = None


def get_tokenizer():
    global _jieba

    if _jieba is None:
        import jieba

        for word in ("干宸浩", "张谢童甲", "王恩博", "欧阳慷", "超音速"):
            jieba.add_word(word)

        _jieba = jieba

    return _jieba


STOPWORDS = {
    "的",
    "了",
    "是",
    "有",
    "什么",
    "吗",
    "呢",
    "啊",
    "？",
    "?",
    "，",
    ",",
    "。",
    ".",
    "！",
    "!"
}


def tokenize(text: str) -> list[str]:
    jieba = get_tokenizer()
    tokens = jieba.lcut(text)

    clean_tokens = []

    for token in tokens:
        token = token.strip()

        if not token:
            continue

        if token in STOPWORDS:
            continue

        clean_tokens.append(token)

    return clean_tokens
