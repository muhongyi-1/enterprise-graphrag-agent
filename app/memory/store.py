from dataclasses import (
    dataclass
)

from datetime import (
    datetime,
    timezone
)

from threading import (
    RLock
)


# ============================================================
# Long-term Memory Item
# ============================================================

@dataclass
class MemoryItem:

    key: str

    value: str

    text: str

    importance: float = 0.5

    updated_at: str = ""


# ============================================================
# Long-term Memory Store
#
# 当前：
#
# In-Memory
#
# 生产：
#
# PostgreSQL / Redis / Vector Store
# ============================================================

class LongTermMemoryStore:

    def __init__(self):

        # user_id
        #   ↓
        # key
        #   ↓
        # MemoryItem

        self._data = {}

        self._lock = RLock()


    # ========================================================
    # Upsert
    #
    # 相同 key：
    #
    # 新值覆盖旧值
    #
    # 解决简单结构化Memory冲突。
    # ========================================================

    def upsert(

            self,

            user_id: str,

            item: MemoryItem
    ):

        if not item.updated_at:

            item.updated_at = (

                datetime.now(
                    timezone.utc
                ).isoformat()
            )


        with self._lock:

            user_memory = (
                self._data.setdefault(
                    user_id,
                    {}
                )
            )


            user_memory[
                item.key
            ] = item


    def get_all(
            self,
            user_id: str
    ):

        with self._lock:

            values = (

                self._data.get(
                    user_id,
                    {}
                ).values()
            )


            return list(
                values
            )


    # ========================================================
    # 简单 Query-aware Retrieval
    #
    # 当前Memory数量很少，
    # 采用：
    #
    # relevance + importance
    #
    # 正式项目后：
    #
    # 可以升级Embedding Retrieval。
    # ========================================================

    def search(

            self,

            user_id: str,

            query: str,

            top_k: int = 3
    ):

        memories = (
            self.get_all(
                user_id
            )
        )


        query_lower = (
            query.lower()
        )


        scored = []


        for item in memories:

            score = (
                item.importance
            )


            # key相关
            if (
                item.key.lower()
                in query_lower
            ):

                score += 1


            # value相关
            if (
                item.value.lower()
                in query_lower
            ):

                score += 1


            # 目前Memory不多，
            # importance保证重要Memory仍有机会进入Context。

            scored.append(
                (
                    score,
                    item
                )
            )


        scored.sort(

            key=lambda pair:
                pair[0],

            reverse=True
        )


        return [

            item

            for score, item
            in scored[:top_k]
        ]


# ============================================================
# 全局Store
# ============================================================

memory_store = (
    LongTermMemoryStore()
)