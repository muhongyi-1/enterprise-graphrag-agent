import re

from app.memory.store import (
    MemoryItem,
    memory_store
)

from app.core.observability import (
    logger
)


# ============================================================
# 目前是第一版规则型 Memory Extractor。
#
# 以后升级：
#
# LLM Structured Output
# ↓
# Memory Candidate
# ↓
# Validation
# ↓
# Store
# ============================================================

def extract_memories(
        text: str
):

    memories = []


    # ========================================================
    # Programming Language
    #
    # 支持：
    #
    # 我主要使用Java
    # 以后默认用Python
    # 后续使用C++
    # ========================================================

    language_pattern = re.compile(

        r"(?:主要使用|默认使用|默认用|以后使用|以后用|后续使用|后续用)"
        r"\s*"
        r"(Java|Python|C\+\+|Go|Golang)",

        re.IGNORECASE
    )


    match = language_pattern.search(
        text
    )


    if match:

        language = (
            match.group(1)
        )


        memories.append(

            MemoryItem(

                key=
                    "preferred_language",

                value=
                    language,

                text=(
                    f"用户默认使用"
                    f"{language}进行编程。"
                ),

                importance=
                    1.0
            )
        )


    # ========================================================
    # 回答风格
    # ========================================================

    if (
        "回答尽量简洁"
        in text
        or
        "回答简洁"
        in text
    ):

        memories.append(

            MemoryItem(

                key=
                    "response_style",

                value=
                    "concise",

                text=
                    "用户偏好简洁回答。",

                importance=
                    0.8
            )
        )


    return memories


# ============================================================
# Extract + Save
# ============================================================

def save_memories_from_message(

        user_id: str,

        text: str
):

    memories = (
        extract_memories(
            text
        )
    )


    for item in memories:

        memory_store.upsert(

            user_id,

            item
        )


        logger.info(

            "Long-term memory saved",

            extra={

                "event":
                    "memory_saved"
            }
        )


    return memories