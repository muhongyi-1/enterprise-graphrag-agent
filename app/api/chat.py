from fastapi import (
    APIRouter,
    HTTPException
)

from langchain_core.messages import (
    HumanMessage
)

from app.agent.graph import (
    graph
)

from app.schemas.chat import (
    ChatRequest,
    ChatResponse
)

from app.core.observability import (
    logger,
    push_context,
    pop_context
)

from app.memory.extractor import (
    save_memories_from_message
)


router = APIRouter(
    prefix="/chat",
    tags=[
        "Chat"
    ]
)


@router.post(
    "",
    response_model=ChatResponse
)
async def chat(
        request: ChatRequest
):

    tokens = push_context(
        user_id=request.user_id,
        thread_id=request.thread_id
    )

    config = {
        "configurable": {
            "thread_id":
                request.thread_id
        }
    }

    try:

        print(
            "\n"
            "============================================================",
            flush=True
        )

        print(
            "进入 /chat",
            flush=True
        )

        print(
            "user_id：",
            request.user_id,
            flush=True
        )

        print(
            "thread_id：",
            request.thread_id,
            flush=True
        )

        print(
            "message：",
            request.message,
            flush=True
        )

        print(
            "============================================================",
            flush=True
        )

        logger.info(
            "Chat request received",
            extra={
                "event":
                    "chat_request_received"
            }
        )

        print(
            "\n[DEBUG] 准备执行 "
            "save_memories_from_message",
            flush=True
        )

        save_memories_from_message(
            user_id=request.user_id,
            text=request.message
        )

        print(
            "[DEBUG] "
            "save_memories_from_message 执行完成",
            flush=True
        )

        print(
            "\n[DEBUG] 准备执行 graph.aget_state",
            flush=True
        )

        old_state = await graph.aget_state(
            config
        )

        print(
            "[DEBUG] graph.aget_state 执行完成",
            flush=True
        )

        old_messages = (
            old_state.values.get(
                "messages",
                []
            )
            if old_state.values
            else []
        )

        print()
        print(
            "=" * 60,
            flush=True
        )

        print(
            "当前 Thread：",
            request.thread_id,
            flush=True
        )

        print(
            "执行前历史消息数量：",
            len(
                old_messages
            ),
            flush=True
        )

        if not old_messages:
            print(
                "当前 Checkpoint 中暂无历史消息。",
                flush=True
            )

        for index, message in enumerate(
            old_messages,
            start=1
        ):
            print(
                f"{index}.",
                type(message).__name__,
                "：",
                message.content,
                flush=True
            )

        print(
            "=" * 60,
            flush=True
        )

        print(
            "\n[DEBUG] 准备执行 graph.ainvoke",
            flush=True
        )

        result = await graph.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        content=request.message
                    )
                ],
                "user_id":
                    request.user_id,
                "thread_id":
                    request.thread_id
            },
            config=config
        )

        print(
            "[DEBUG] graph.ainvoke 执行完成",
            flush=True
        )

        print(
            "\n[DEBUG] 准备再次读取 Checkpoint",
            flush=True
        )

        new_state = await graph.aget_state(
            config
        )

        print(
            "[DEBUG] 第二次 graph.aget_state 执行完成",
            flush=True
        )

        new_messages = (
            new_state.values.get(
                "messages",
                []
            )
            if new_state.values
            else []
        )

        print()
        print(
            "=" * 60,
            flush=True
        )

        print(
            "执行后历史消息数量：",
            len(
                new_messages
            ),
            flush=True
        )

        for index, message in enumerate(
            new_messages,
            start=1
        ):
            print(
                f"{index}.",
                type(message).__name__,
                "：",
                message.content,
                flush=True
            )

        print(
            "=" * 60,
            flush=True
        )

        final_message = (
            result[
                "messages"
            ][-1]
        )

        logger.info(
            "Chat request completed",
            extra={
                "event":
                    "chat_request_completed"
            }
        )

        print(
            "\n[DEBUG] /chat 请求处理完成",
            flush=True
        )

        print(
            "============================================================\n",
            flush=True
        )

        return ChatResponse(
            answer=final_message.content
        )

    except Exception as exc:

        print()
        print(
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
            flush=True
        )

        print(
            "[ERROR] /chat 执行失败",
            flush=True
        )

        print(
            "异常类型：",
            type(exc).__name__,
            flush=True
        )

        print(
            "异常信息：",
            str(exc),
            flush=True
        )

        print(
            "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",
            flush=True
        )

        logger.exception(
            "Agent execution failed",
            extra={
                "event":
                    "agent_execution_failed",
                "error_type":
                    type(exc).__name__
            }
        )

        raise HTTPException(
            status_code=500,
            detail="Agent执行失败"
        )

    finally:
        pop_context(
            tokens
        )