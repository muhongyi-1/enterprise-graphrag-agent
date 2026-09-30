from collections import (
    defaultdict
)

def rrf_fusion(
        result_lists,
        k: int = 60,
        top_k: int = 10
):

    scores = defaultdict(float)
    documents = {}

    for results in result_lists:
        for rank, document in enumerate(results, start=1):
            document_id = document["id"]
            scores[document_id] += 1.0 / (k + rank)
            documents[document_id] = document

    ranked_ids = sorted(
        scores.keys(),
        key=lambda doc_id: scores[doc_id],
        reverse=True
    )

    fused_results = []

    for document_id in ranked_ids[:top_k]:
        document = dict(documents[document_id])
        document["rrf_score"] = scores[document_id]
        fused_results.append(document)

    return fused_results