import asyncio
import time

from app.rag.vector_retriever import (
    vector_search
)

from app.rag.bm25_retriever import (
    bm25_search
)

from app.rag.fusion import (
    rrf_fusion
)

from app.rag.reranker import (
    rerank
)

from app.rag.graph_retriever import (
    graph_search
)

from app.core.observability import (
    logger
)


async def hybrid_search(
        query: str,
        recall_top_k: int = 5,
        fusion_top_k: int = 6,
        final_top_k: int = 3
):

    start_time = time.perf_counter()

    logger.info(
        "Hybrid retrieval started",
        extra={
            "event":
                "hybrid_retrieval_started"
        }
    )

    try:

        vector_task = asyncio.to_thread(
            vector_search,
            query,
            recall_top_k
        )

        bm25_task = asyncio.to_thread(
            bm25_search,
            query,
            recall_top_k
        )

        vector_results, bm25_results = (
            await asyncio.gather(
                vector_task,
                bm25_task
            )
        )

        logger.info(
            "Multi-retriever recall finished",
            extra={
                "event":
                    "retrieval_recall_finished"
            }
        )

        fused_results = rrf_fusion(
            [
                vector_results,
                bm25_results
            ],
            top_k=fusion_top_k
        )

        logger.info(
            "RRF fusion finished",
            extra={
                "event":
                    "rrf_fusion_finished"
            }
        )

        final_results = (
            await asyncio.to_thread(
                rerank,
                query,
                fused_results,
                final_top_k
            )
        )

        logger.info(
            "Rerank finished",
            extra={
                "event":
                    "rerank_finished"
            }
        )

        return final_results

    except Exception as exc:

        logger.exception(
            "Hybrid retrieval failed",
            extra={
                "event":
                    "hybrid_retrieval_failed",
                "error_type":
                    type(exc).__name__
            }
        )

        raise

    finally:

        duration_ms = (
            (
                time.perf_counter()
                -
                start_time
            )
            *
            1000
        )

        logger.info(
            "Hybrid retrieval finished",
            extra={
                "event":
                    "hybrid_retrieval_finished",
                "duration_ms":
                    round(
                        duration_ms,
                        2
                    )
            }
        )


async def retrieve_knowledge(
        query: str
):

    start_time = time.perf_counter()

    logger.info(
        "Knowledge retrieval started",
        extra={
            "event":
                "knowledge_retrieval_started"
        }
    )

    try:

        text_task = hybrid_search(
            query
        )

        graph_task = asyncio.to_thread(
            graph_search,
            query
        )

        text_results, graph_results = (
            await asyncio.gather(
                text_task,
                graph_task
            )
        )

        logger.info(
            "Knowledge retrieval finished",
            extra={
                "event":
                    "knowledge_retrieval_finished"
            }
        )

        return {
            "text_results":
                text_results,
            "graph_results":
                graph_results
        }

    except Exception as exc:

        logger.exception(
            "Knowledge retrieval failed",
            extra={
                "event":
                    "knowledge_retrieval_failed",
                "error_type":
                    type(exc).__name__
            }
        )

        raise

    finally:

        duration_ms = (
            (
                time.perf_counter()
                -
                start_time
            )
            *
            1000
        )

        logger.info(
            "Knowledge retrieval latency recorded",
            extra={
                "event":
                    "knowledge_retrieval_latency",
                "duration_ms":
                    round(
                        duration_ms,
                        2
                    )
            }
        )