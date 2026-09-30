from sentence_transformers import (
    CrossEncoder
)

from app.core.observability import (
    logger
)

reranker_model = CrossEncoder(
    "BAAI/bge-reranker-base"
)

def rerank(
        query: str,
        documents,
        top_k: int = 3
):

    if not documents:
        return []

    logger.info(
        "Rerank started",
        extra={
            "event":
                "rerank_started"
        }
    )

    pairs = [
        [query, document["content"]]
        for document in documents
    ]

    scores = reranker_model.predict(
        pairs
    )

    ranked = []

    for document, score in zip(
        documents,
        scores
    ):
        item = dict(document)
        item["rerank_score"] = float(score)
        ranked.append(item)

    ranked.sort(
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    logger.info(
        "Rerank finished",
        extra={
            "event":
                "rerank_finished"
        }
    )

    return ranked[:top_k]