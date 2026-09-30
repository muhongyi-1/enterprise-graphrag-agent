from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    前端调用 POST /chat 时传入的数据。
    """

    user_id: str = Field(
        ...,
        description="用户唯一标识"
    )

    thread_id: str = Field(
        ...,
        description="当前会话唯一标识"
    )

    message: str = Field(
        ...,
        min_length=1,
        description="用户输入内容"
    )


class ChatResponse(BaseModel):
    """
    /chat 返回给前端的数据。
    """

    answer: str