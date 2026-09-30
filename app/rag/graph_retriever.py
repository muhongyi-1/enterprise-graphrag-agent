from neo4j.exceptions import (
    Neo4jError,
    ServiceUnavailable
)

from app.services.neo4j import (
    neo4j_driver
)

from app.core.observability import (
    logger
)

def extract_graph_keywords(
        query: str
):

    query_lower = query.lower()

    candidates = [
        "graphrag",
        "neo4j",
        "pgvector",
        "postgresql",
        "langgraph",
        "bm25",
        "rrf",
        "rerank",
        "实体关系",
        "文本向量"
    ]

    return [
        keyword
        for keyword in candidates
        if keyword.lower() in query_lower
    ]

def graph_search(
        query: str,
        limit: int = 10
):

    logger.info(
        "Graph search started",
        extra={
            "event":"graph_search_started"
        }
    )

    keywords = extract_graph_keywords(query)

    if not keywords:
        logger.info(
            "Graph search skipped",
            extra={
                "event":"graph_search_skipped"
            }
        )
        return []

    results = []

    try:
        with neo4j_driver.session() as session:
            for keyword in keywords:
                records = session.run(
                    """
                    MATCH (n)
                    WHERE toLower(coalesce(n.name,'')) CONTAINS toLower($keyword)
                    OPTIONAL MATCH (n)-[r]-(m)
                    RETURN
                        labels(n) AS source_labels,
                        n.name AS source,
                        type(r) AS relation,
                        labels(m) AS target_labels,
                        m.name AS target
                    LIMIT $limit
                    """,
                    keyword=keyword,
                    limit=limit
                )

                for record in records:
                    source = record["source"]
                    relation = record["relation"]
                    target = record["target"]

                    if relation is None or target is None:
                        continue

                    item = {
                        "source":source,
                        "relation":relation,
                        "target":target,
                        "text":f"{source} --[{relation}]--> {target}"
                    }

                    if item not in results:
                        results.append(item)

        logger.info(
            "Graph search finished",
            extra={
                "event":"graph_search_finished"
            }
        )
        return results

    except (
        ServiceUnavailable,
        Neo4jError
    ) as exc:
        logger.warning(
            "Neo4j unavailable, graph retrieval degraded",
            extra={
                "event":"graph_search_degraded",
                "error_type":type(exc).__name__
            }
        )
        return []