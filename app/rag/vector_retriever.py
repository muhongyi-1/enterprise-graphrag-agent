import numpy as np

from sentence_transformers import (
    SentenceTransformer
)

from app.rag.documents import (
    DOCUMENTS
)

from app.core.observability import (
    logger
)

embedding_model = SentenceTransformer(
    "BAAI/bge-small-zh-v1.5"
)

_document_texts = [
    document["content"]
    for document in DOCUMENTS
]

_document_embeddings = (
    embedding_model.encode(
        _document_texts,
        normalize_embeddings=True,
        convert_to_numpy=True
    )
)

def vector_search(
        query: str,
        top_k: int = 5
):

    logger.info(
        "Vector search started",
        extra={
            "event":
                "vector_search_started"
        }
    )

    query_embedding = (
        embedding_model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True
        )[0]
    )

    scores = np.dot(
        _document_embeddings,
        query_embedding
    )

    indices = np.argsort(
        scores
    )[::-1]

    results = []

    for index in indices[:top_k]:
        document = DOCUMENTS[int(index)]
        results.append({
            "id":document["id"],
            "content":document["content"],
            "metadata":document["metadata"],
            "score":float(scores[index]),
            "retriever":"vector"
        })

    logger.info(
        "Vector search finished",
        extra={
            "event":
                "vector_search_finished"
        }
    )

    return results