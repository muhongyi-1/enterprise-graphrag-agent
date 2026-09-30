from langchain_core.messages import (
    SystemMessage,
    HumanMessage
)

from app.memory.store import (
    memory_store
)

from app.core.observability import (
    logger
)


# ============================================================
# Context Manager
#
# 核心任务：
#
# Gather
# ↓
# Resolve
# ↓
# Budget
# ↓
# Assemble
# ============================================================

class ContextManager:

    def __init__(
            self,
            recent_message_limit: int = 10,
            memory_top_k: int = 3
    ):

        self.recent_message_limit = (
            recent_message_limit
        )

        self.memory_top_k = (
            memory_top_k
        )


    def _get_current_query(
            self,
            messages
    ):

        for message in reversed(
            messages
        ):

            if isinstance(
                message,
                HumanMessage
            ):

                return str(
                    message.content
                )

        return ""


    def build_messages(
            self,
            *,
            state,
            base_system_prompt: str
    ):

        messages = state["messages"]
        user_id = state["user_id"]

        query = self._get_current_query(
            messages
        )

        memories = memory_store.search(
            user_id=user_id,
            query=query,
            top_k=self.memory_top_k
        )

        memory_text = "\n".join(
            f"- {item.text}"
            for item in memories
        )

        if not memory_text:
            memory_text = "暂无相关长期记忆。"

        system_prompt = f"""
{base_system_prompt}

【Context规则】

信息优先级：

1. 当前用户本轮明确要求
2. 当前Thread最近对话
3. 长期Memory

如果当前用户输入和旧Memory冲突，
必须优先遵循当前输入。


【当前用户长期Memory】

{memory_text}
""".strip()

        recent_messages = messages[
            -self.recent_message_limit:
        ]

        logger.info(
            "Context assembled",
            extra={
                "event":
                    "context_assembled"
            }
        )

        return [
            SystemMessage(
                content=system_prompt
            ),
            *recent_messages
        ]


context_manager = (
    ContextManager()
)