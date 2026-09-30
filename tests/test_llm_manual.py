from app.services.llm import llm


def main():

    print(
        "开始测试 LLM..."
    )

    response = llm.invoke(
        "请只回答一句话：什么是Agent？"
    )

    print()
    print(
        "模型返回："
    )

    print(
        response.content
    )


if __name__ == "__main__":

    main()