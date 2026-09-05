import math


# TF
def term_frequency(term: str, document: list[str]) -> int:
    count = 0

    for token in document:
        if term == token:
            count += 1

    return count


# DF
def document_frequency(term: str, documents: list[list[str]]) -> int:
    count = 0

    for document in documents:
        if term in document:
            count += 1

    return count


# IDF 词多稀有 越稀有值越大
def inverse_document_frequency(
    term: str,
    documents: list[list[str]]
) -> float:

    document_count = len(documents)

    df = document_frequency(term, documents)

    if df == 0:
        raise ValueError("该词没有出现在任何文档中")

    idf = math.log(document_count / df)

    return idf


"""
dl = document length = 当前文档长度

avgdl = average document length = 整个知识库的平均文档长度

b = 文档长度影响程度
"""
def average_document_length(
    documents: list[list[str]]
) -> float:

    total_length = 0

    for document in documents:
        total_length += len(document)

    average_length = total_length / len(documents)

    return average_length


def bm25_tf_component(
    tf: int,
    document_length: int,
    average_length: float,
    k1: float = 1.5,
    b: float = 0.75
) -> float:

    length_normalization = (
        1 - b + b * document_length / average_length
    )

    numerator = tf * (k1 + 1)

    denominator = (
        tf + k1 * length_normalization
    )

    return numerator / denominator


def bm25_term_score(
    term: str,
    document: list[str],
    documents: list[list[str]],
    k1: float = 1.5,
    b: float = 0.75
) -> float:
    
    df = document_frequency(term, documents)
    if df == 0:
        return 0.0
    
    tf = term_frequency(term, document)

    idf = inverse_document_frequency(term, documents)

    document_length = len(document)

    average_length = average_document_length(documents)

    tf_component = bm25_tf_component(
        tf=tf,
        document_length=document_length,
        average_length=average_length,
        k1=k1,
        b=b
    )

    return idf * tf_component


def bm25_query_score(
    query: list[str],
    document: list[str],
    documents: list[list[str]],
    k1: float = 1.5,
    b: float = 0.75
) -> float:

    total_score = 0.0

    for term in query:
        term_score = bm25_term_score(
                        term,
                        document,
                        documents,
                        k1,
                        b
                    )

        total_score += term_score

    return total_score
