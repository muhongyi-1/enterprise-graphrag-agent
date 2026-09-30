import asyncio

from app.rag.pipeline import (
    retrieve_knowledge
)


async def main():

    query = (
        "GraphRAG中的实体关系存在哪里？"
    )

    result = await retrieve_knowledge(
        query
    )

    print()
    print("=" * 60)
    print("Text Results")
    print("=" * 60)

    for item in result[
        "text_results"
    ]:
        print()
        print(item["id"], item["content"])

    print()
    print("=" * 60)
    print("Graph Results")
    print("=" * 60)

    for item in result[
        "graph_results"
    ]:
        print(item["text"])


if __name__ == "__main__":
    asyncio.run(main())