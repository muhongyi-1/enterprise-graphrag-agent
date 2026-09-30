import time

from langchain_core.messages import (
    AIMessage
)

from app.agent.state import (
    AgentState
)

from app.services.llm import (
    llm
)

from app.tools.knowledge import (
    search_knowledge
)

from app.core.reliability import (
    run_with_retry,
    RetryExhaustedError,
    LLM_RETRYABLE_EXCEPTIONS,
    llm_semaphore
)

from app.core.observability import (
    logger,
    LLM_CALLS,
    LLM_LATENCY
)

from app.memory.context_manager import (
    context_manager
)

tools = [
    search_knowledge
]

llm_with_tools = (
    llm.bind_tools(
        tools
    )
)

SYSTEM_PROMPT = """
你是一个企业知识库智能Agent。

要求：

1. 如果用户询问企业内部项目、GraphRAG架构、
   RAG流程、Neo4j、pgvector、BM25、RRF、
   Rerank、LangGraph、Memory等内部知识，
   应优先调用search_knowledge工具获取证据。

2. search_knowledge工具内部可能返回：
   文本检索证据和Neo4j图谱关系证据。
   回答企业内部事实时，应优先依据这些证据。

3. 如果只是普通常识问题，
   可以直接回答，不必强行调用工具。

4. 如果工具没有查到相关信息，
   不要编造企业内部事实。

5. 如果当前用户明确要求和历史Memory冲突，
   应优先遵循当前用户本轮明确要求。

6. 回答尽量清晰、简洁。
""".strip()

async def agent_node(
        state: AgentState
) -> dict:

    input_messages = (
        context_manager.build_messages(
            state=state,
            base_system_prompt=SYSTEM_PROMPT
        )
    )

    llm_start = (
        time.perf_counter()
    )

    logger.info(
        "LLM call started",
        extra={
            "event":
                "llm_call_started"
        }
    )

    try:

        response = await run_with_retry(
            operation=lambda: (
                llm_with_tools.ainvoke(
                    input_messages
                )
            ),
            service_name="DeepSeek",
            timeout_seconds=20,
            max_attempts=3,
            base_delay_seconds=0.5,
            retry_exceptions=LLM_RETRYABLE_EXCEPTIONS,
            semaphore=llm_semaphore
        )

        LLM_CALLS.labels(
            status="success"
        ).inc()

        logger.info(
            "LLM call finished",
            extra={
                "event":"llm_call_finished",
                "tool_calls_count":len(response.tool_calls)
            }
        )

    except RetryExhaustedError as exc:

        LLM_CALLS.labels(
            status="failed"
        ).inc()

        logger.error(
            "LLM call exhausted retries",
            extra={
                "event":"llm_call_failed",
                "error_type":type(exc).__name__
            }
        )

        return {
            "messages": [
                AIMessage(
                    content=(
                        "当前模型服务暂时不可用，"
                        "请稍后再试。"
                    )
                )
            ]
        }

    finally:

        llm_duration = (
            time.perf_counter()
            -
            llm_start
        )

        LLM_LATENCY.observe(
            llm_duration
        )

        logger.info(
            "LLM latency recorded",
            extra={
                "event":"llm_latency",
                "duration_ms":round(
                    llm_duration * 1000,
                    2
                )
            }
        )

    if response.tool_calls:

        logger.info(
            "Agent decided to call tools",
            extra={
                "event":"agent_tool_decision",
                "tool_calls_count":len(response.tool_calls)
            }
        )

        for tool_call in response.tool_calls:
            logger.info(
                "Tool selected",
                extra={
                    "event":"tool_selected",
                    "tool_name":tool_call["name"]
                }
            )

    else:
        logger.info(
            "Agent generated answer",
            extra={
                "event":"agent_final_answer"
            }
        )

    return {
        "messages": [
            response
        ]
    }