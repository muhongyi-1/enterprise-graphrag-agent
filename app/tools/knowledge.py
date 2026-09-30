import time
import json

from langchain_core.tools import (
    tool
)

from app.rag.pipeline import (
    retrieve_knowledge
)

from app.core.observability import (
    logger,
    TOOL_CALLS,
    TOOL_LATENCY
)


def _get_graph_value(
        item: dict,
        *keys,
        default="unknown"
):

    for key in keys:
        value = item.get(key)
        if value is not None:
            return value

    return default


def _format_graph_evidence(
        graph_item,
        index: int
) -> str:

    if isinstance(
        graph_item,
        dict
    ):

        entity = _get_graph_value(
            graph_item,
            "entity",
            "source_entity",
            "source",
            "start_entity"
        )

        relation = _get_graph_value(
            graph_item,
            "relation",
            "relationship",
            "relation_type",
            "type"
        )

        target_entity = _get_graph_value(
            graph_item,
            "target_entity",
            "target",
            "end_entity"
        )

        relation_path = _get_graph_value(
            graph_item,
            "path",
            "relation_path",
            "relationship_path"
        )

        raw_data = json.dumps(
            graph_item,
            ensure_ascii=False,
            default=str
        )

        return (
            f"[图谱证据{index}]\n"
            f"实体：{entity}\n"
            f"关系：{relation}\n"
            f"目标实体：{target_entity}\n"
            f"关系路径：{relation_path}\n"
            f"原始数据：{raw_data}"
        )

    return (
        f"[图谱证据{index}]\n"
        f"原始数据：{graph_item}"
    )


@tool
async def search_knowledge(
        query: str
) -> str:
    """
    查询企业内部知识库。

    同时使用：

    1. Hybrid Text RAG
       Vector + BM25 → RRF → Rerank

    2. Graph Retrieval
       Neo4j

    当 Neo4j 不可用时，
    Graph Retrieval 应降级为空结果，
    Text RAG 仍然可以继续工作。

    Args:
        query:
            用户需要查询的问题。

    Returns:
        文本证据和图谱证据。
    """

    tool_name = (
        "search_knowledge"
    )

    start_time = (
        time.perf_counter()
    )

    logger.info(
        "Tool execution started",
        extra={
            "event":
                "tool_started",
            "tool_name":
                tool_name
        }
    )

    try:

        retrieval_result = (
            await retrieve_knowledge(
                query
            )
        )

        documents = (
            retrieval_result.get(
                "text_results",
                []
            )
            or []
        )

        graph_results = (
            retrieval_result.get(
                "graph_results",
                []
            )
            or []
        )

        print()
        print(
            "=" * 60,
            flush=True
        )

        print(
            "[Knowledge Retrieval DEBUG]",
            flush=True
        )

        print(
            "Query：",
            query,
            flush=True
        )

        print(
            "Text Results 数量：",
            len(documents),
            flush=True
        )

        print(
            "Graph Results 数量：",
            len(graph_results),
            flush=True
        )

        for index, graph_item in enumerate(
            graph_results,
            start=1
        ):
            print(
                f"Graph Result {index}：",
                graph_item,
                flush=True
            )

        print(
            "=" * 60,
            flush=True
        )

        evidence_blocks = []

        for index, document in enumerate(
            documents,
            start=1
        ):

            metadata = (
                document.get(
                    "metadata",
                    {}
                )
                or {}
            )

            source = metadata.get(
                "source",
                "unknown"
            )

            section = metadata.get(
                "section",
                "unknown"
            )

            document_id = document.get(
                "id",
                "unknown"
            )

            content = document.get(
                "content",
                ""
            )

            evidence_blocks.append(
                (
                    f"[文本证据{index}]\n"
                    f"文档ID：{document_id}\n"
                    f"来源：{source}\n"
                    f"章节：{section}\n"
                    f"内容：{content}"
                )
            )

        for index, graph_item in enumerate(
            graph_results,
            start=1
        ):
            evidence_blocks.append(
                _format_graph_evidence(
                    graph_item,
                    index
                )
            )

        if not evidence_blocks:
            result = (
                "当前企业知识库中没有检索到"
                "足够相关的文本证据或图谱证据。"
            )
        else:
            result = "\n\n".join(
                evidence_blocks
            )

        print()
        print(
            "[Knowledge Tool Result]",
            flush=True
        )

        print(
            result,
            flush=True
        )

        print(
            "=" * 60,
            flush=True
        )

        TOOL_CALLS.labels(
            tool_name=tool_name,
            status="success"
        ).inc()

        logger.info(
            "Tool execution finished",
            extra={
                "event":
                    "tool_finished",
                "tool_name":
                    tool_name,
                "status":
                    "success"
            }
        )

        return result

    except Exception as exc:

        TOOL_CALLS.labels(
            tool_name=tool_name,
            status="failed"
        ).inc()

        logger.exception(
            "Tool execution failed",
            extra={
                "event":
                    "tool_failed",
                "tool_name":
                    tool_name,
                "status":
                    "failed",
                "error_type":
                    type(exc).__name__
            }
        )

        raise

    finally:

        duration = (
            time.perf_counter()
            -
            start_time
        )

        TOOL_LATENCY.labels(
            tool_name=tool_name
        ).observe(
            duration
        )

        logger.info(
            "Tool latency recorded",
            extra={
                "event":
                    "tool_latency",
                "tool_name":
                    tool_name,
                "duration_ms":
                    round(
                        duration
                        *
                        1000,
                        2
                    )
            }
        )