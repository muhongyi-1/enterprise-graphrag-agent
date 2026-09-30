import asyncio

from app.rag.pipeline import (
    hybrid_search
)


async def main():

    query = (
        "GraphRAG中的实体关系存在哪里？"
    )


    results = await hybrid_search(
        query
    )


    print()
    print("=" * 70)

    print(
        "Query：",
        query
    )

    print("=" * 70)


    for index, document in enumerate(

        results,

        start=1
    ):

        print()

        print(
            f"Top {index}"
        )

        print(
            "ID：",
            document["id"]
        )

        print(
            "Content：",
            document["content"]
        )

        print(
            "RRF：",
            document.get(
                "rrf_score"
            )
        )

        print(
            "Rerank：",
            document.get(
                "rerank_score"
            )
        )


if __name__ == "__main__":

    asyncio.run(
        main()
    )