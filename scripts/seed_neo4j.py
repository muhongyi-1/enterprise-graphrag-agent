from app.services.neo4j import (
    neo4j_driver
)


CYPHER = """
MERGE (project:Project {
    name: 'GraphRAG'
})

MERGE (neo4j:Technology {
    name: 'Neo4j',
    type: 'Graph Database'
})

MERGE (pgvector:Technology {
    name: 'pgvector',
    type: 'Vector Database Extension'
})

MERGE (postgres:Technology {
    name: 'PostgreSQL',
    type: 'Relational Database'
})

MERGE (langgraph:Technology {
    name: 'LangGraph',
    type: 'Agent Orchestration'
})

MERGE (bm25:Algorithm {
    name: 'BM25'
})

MERGE (rrf:Algorithm {
    name: 'RRF'
})

MERGE (reranker:Algorithm {
    name: 'Cross Encoder Reranker'
})

MERGE (project)-[:USES]->(neo4j)

MERGE (project)-[:USES]->(pgvector)

MERGE (project)-[:USES]->(postgres)

MERGE (project)-[:USES]->(langgraph)

MERGE (project)-[:USES_ALGORITHM]->(bm25)

MERGE (project)-[:USES_ALGORITHM]->(rrf)

MERGE (project)-[:USES_ALGORITHM]->(reranker)

MERGE (neo4j)-[:STORES]->(
    entity:Concept {
        name: '实体关系'
    }
)

MERGE (pgvector)-[:STORES]->(
    vector:Concept {
        name: '文本向量'
    }
)
"""


def main():

    with neo4j_driver.session() as session:

        session.run(
            CYPHER
        )

    print(
        "Neo4j Graph 初始化完成"
    )


if __name__ == "__main__":

    main()