import jieba

from rank_bm25 import (
    BM25Okapi
)

from app.rag.documents import (
    DOCUMENTS
)

from app.core.observability import (
    logger
)

def tokenize(
        text: str
):

    return [
        token.strip().lower()
        for token in jieba.lcut(text)
        if token.strip()
    ]

_tokenized_documents = [
    tokenize(document["content"])
    for document in DOCUMENTS
]

bm25 = BM25Okapi(
    _tokenized_documents
)

def bm25_search(
        query: str,
        top_k: int = 5
):

    logger.info(
        "BM25 search started",
        extra={
            "event":
                "bm25_search_started"
        }
    )

    query_tokens = tokenize(query)
    scores = bm25.get_scores(query_tokens)

    indices = sorted(
        range(len(DOCUMENTS)),
        key=lambda index: scores[index],
        reverse=True
    )

    results = []

    for index in indices[:top_k]:
        document = DOCUMENTS[index]
        results.append({
            "id":document["id"],
            "content":document["content"],
            "metadata":document["metadata"],
            "score":float(scores[index]),
            "retriever":"bm25"
        })

    logger.info(
        "BM25 search finished",
        extra={
            "event":
                "bm25_search_finished"
        }
    )

    return results