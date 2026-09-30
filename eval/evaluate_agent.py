import asyncio
import json
import time

from pathlib import Path

from langchain_core.messages import (
    HumanMessage,
    AIMessage
)

from app.agent.graph import (
    graph
)


# ============================================================
# 项目根目录
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


# ============================================================
# Evaluation Dataset
# ============================================================

DATASET_PATH = (

    PROJECT_ROOT

    / "eval"

    / "agent_eval_dataset.json"
)


# ============================================================
# Evaluation Result
# ============================================================

RESULT_PATH = (

    PROJECT_ROOT

    / "eval"

    / "agent_eval_results.json"
)


# ============================================================
# 1. 加载测试集
# ============================================================

def load_dataset():

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(
            file
        )


# ============================================================
# 2. 从 Messages 中提取所有 Tool Call
#
# 一次 Agent 执行可能不止调用一个 Tool。
#
# 所以遍历所有 AIMessage。
# ============================================================

def extract_tool_calls(
        messages
):

    tool_calls = []


    for message in messages:

        if not isinstance(
            message,
            AIMessage
        ):

            continue


        calls = getattr(
            message,
            "tool_calls",
            None
        )


        if calls:

            tool_calls.extend(
                calls
            )


    return tool_calls


# ============================================================
# 3. Tool Selection Evaluation
# ============================================================

def evaluate_tool_selection(
        expected_tool,
        tool_calls
):

    # ========================================================
    # 如果标准答案认为：
    #
    # 不应该调用 Tool
    # ========================================================

    if expected_tool is None:

        return (
            len(tool_calls)
            ==
            0
        )


    # ========================================================
    # 标准答案要求调用某 Tool
    #
    # 只要实际 Tool Call 中存在这个 Tool，
    # 当前版本就认为选择正确。
    # ========================================================

    for call in tool_calls:

        if (
            call.get("name")
            ==
            expected_tool
        ):

            return True


    return False


# ============================================================
# 4. Tool Argument Evaluation
#
# 当前 search_knowledge 的参数是：
#
# query
#
# 所以第一版先检查：
#
# ① 必须字段存在
# ② 值不是空字符串
#
#
# 以后如果有：
#
# query_order(order_id)
#
# 就可以进一步检查：
#
# order_id 是否等于标准答案。
# ============================================================

def evaluate_tool_arguments(
        expected_tool,
        required_args,
        tool_calls
):

    # 不需要 Tool
    if expected_tool is None:

        return True


    # 找到目标 Tool Call
    target_call = None


    for call in tool_calls:

        if (
            call.get("name")
            ==
            expected_tool
        ):

            target_call = call

            break


    # Tool 都没选对
    if target_call is None:

        return False


    arguments = (
        target_call.get(
            "args",
            {}
        )
    )


    # ========================================================
    # 检查必填参数
    # ========================================================

    for argument_name in required_args:

        if argument_name not in arguments:

            return False


        value = arguments[
            argument_name
        ]


        # None
        if value is None:

            return False


        # 空字符串
        if (
            isinstance(
                value,
                str
            )
            and
            not value.strip()
        ):

            return False


    return True


# ============================================================
# 5. Task Completion
#
# 当前采用：
#
# Required Keywords
#
# 进行简单自动评测。
#
#
# 例如标准答案要求：
#
# Neo4j
#
# 最终回答包含 Neo4j
# → Pass
#
#
# 这只是第一版。
#
# 后面还可以升级：
#
# LLM-as-a-Judge
# Semantic Similarity
# Groundedness Judge
# ============================================================

def evaluate_task_completion(
        answer: str,
        required_keywords
):

    answer_lower = (
        answer.lower()
    )


    for keyword in required_keywords:

        if (
            keyword.lower()
            not in answer_lower
        ):

            return False


    return True


# ============================================================
# 6. 评测一个 Case
# ============================================================

async def evaluate_case(
        case: dict
):

    case_id = (
        case["id"]
    )


    query = (
        case["query"]
    )


    expected_tool = (
        case[
            "expected_tool"
        ]
    )


    required_args = (
        case.get(
            "required_tool_args",
            []
        )
    )


    required_keywords = (
        case.get(
            "required_answer_keywords",
            []
        )
    )


    print()
    print("=" * 70)

    print(
        "Evaluation Case：",
        case_id
    )

    print(
        "Query：",
        query
    )

    print("=" * 70)


    # ========================================================
    # 记录整个 Agent Latency
    # ========================================================

    start_time = (
        time.perf_counter()
    )


    try:

        result = await graph.ainvoke(

            {

                "messages": [

                    HumanMessage(
                        content=query
                    )
                ],

                # Evaluation 用独立用户
                "user_id":
                    "eval_user",

                # 每个 Case 使用不同 thread
                "thread_id":
                    f"eval_{case_id}"
            }
        )


        latency_seconds = (

            time.perf_counter()
            -
            start_time
        )


        messages = (
            result[
                "messages"
            ]
        )


        # ====================================================
        # Final Answer
        # ====================================================

        final_message = (
            messages[-1]
        )


        answer = (
            final_message.content
        )


        # ====================================================
        # 提取 Tool Calls
        # ====================================================

        tool_calls = (
            extract_tool_calls(
                messages
            )
        )


        actual_tools = [

            call.get(
                "name"
            )

            for call in tool_calls
        ]


        # ====================================================
        # Tool Selection
        # ====================================================

        tool_selection_correct = (
            evaluate_tool_selection(

                expected_tool,

                tool_calls
            )
        )


        # ====================================================
        # Tool Arguments
        # ====================================================

        tool_arguments_correct = (
            evaluate_tool_arguments(

                expected_tool,

                required_args,

                tool_calls
            )
        )


        # ====================================================
        # Task Completion
        # ====================================================

        task_completed = (
            evaluate_task_completion(

                answer,

                required_keywords
            )
        )


        # ====================================================
        # 整个 Case 是否通过
        # ====================================================

        passed = (

            tool_selection_correct

            and

            tool_arguments_correct

            and

            task_completed
        )


        case_result = {

            "id":
                case_id,

            "category":
                case[
                    "category"
                ],

            "query":
                query,

            "expected_tool":
                expected_tool,

            "actual_tools":
                actual_tools,

            "tool_selection_correct":
                tool_selection_correct,

            "tool_arguments_correct":
                tool_arguments_correct,

            "task_completed":
                task_completed,

            "passed":
                passed,

            "latency_ms":
                round(
                    latency_seconds
                    *
                    1000,

                    2
                ),

            "answer":
                answer
        }


        print(
            "Expected Tool：",
            expected_tool
        )

        print(
            "Actual Tools：",
            actual_tools
        )

        print(
            "Tool Selection：",
            "PASS"
            if tool_selection_correct
            else "FAIL"
        )

        print(
            "Tool Arguments：",
            "PASS"
            if tool_arguments_correct
            else "FAIL"
        )

        print(
            "Task Completion：",
            "PASS"
            if task_completed
            else "FAIL"
        )

        print(
            "Latency：",
            case_result[
                "latency_ms"
            ],
            "ms"
        )

        print(
            "Case：",
            "PASS"
            if passed
            else "FAIL"
        )


        return case_result


    # ========================================================
    # 整个 Agent 执行异常
    # ========================================================

    except Exception as exc:

        latency_seconds = (

            time.perf_counter()
            -
            start_time
        )


        print(
            "Evaluation ERROR：",
            type(
                exc
            ).__name__,
            str(
                exc
            )
        )


        return {

            "id":
                case_id,

            "category":
                case[
                    "category"
                ],

            "query":
                query,

            "expected_tool":
                expected_tool,

            "actual_tools":
                [],

            "tool_selection_correct":
                False,

            "tool_arguments_correct":
                False,

            "task_completed":
                False,

            "passed":
                False,

            "latency_ms":
                round(
                    latency_seconds
                    *
                    1000,

                    2
                ),

            "error":
                type(
                    exc
                ).__name__
        }


# ============================================================
# 7. 汇总指标
# ============================================================

def build_summary(
        results
):

    total = len(
        results
    )


    if total == 0:

        return {}


    tool_selection_correct = sum(

        1

        for result in results

        if result[
            "tool_selection_correct"
        ]
    )


    tool_arguments_correct = sum(

        1

        for result in results

        if result[
            "tool_arguments_correct"
        ]
    )


    task_completed = sum(

        1

        for result in results

        if result[
            "task_completed"
        ]
    )


    passed = sum(

        1

        for result in results

        if result[
            "passed"
        ]
    )


    average_latency = (

        sum(

            result[
                "latency_ms"
            ]

            for result in results
        )

        /

        total
    )


    return {

        "total_cases":
            total,

        "tool_selection_accuracy":
            round(
                tool_selection_correct
                /
                total,
                4
            ),

        "tool_argument_accuracy":
            round(
                tool_arguments_correct
                /
                total,
                4
            ),

        "task_completion_rate":
            round(
                task_completed
                /
                total,
                4
            ),

        "overall_pass_rate":
            round(
                passed
                /
                total,
                4
            ),

        "average_latency_ms":
            round(
                average_latency,
                2
            )
    }


# ============================================================
# 8. Main
# ============================================================

async def main():

    dataset = (
        load_dataset()
    )


    print()
    print("#" * 70)

    print(
        "Agent Evaluation Started"
    )

    print(
        "Cases：",
        len(
            dataset
        )
    )

    print("#" * 70)


    results = []


    # ========================================================
    # 先串行执行。
    #
    # 为什么不直接 asyncio.gather？
    #
    # 因为 Evaluation 第一版优先：
    #
    # 稳定
    # 可观察
    # 容易定位 Bad Case
    #
    # 而且避免一次压大量 LLM 请求。
    # ========================================================

    for case in dataset:

        result = await evaluate_case(
            case
        )

        results.append(
            result
        )


    # ========================================================
    # Summary
    # ========================================================

    summary = (
        build_summary(
            results
        )
    )


    output = {

        "summary":
            summary,

        "results":
            results
    }


    # ========================================================
    # 保存 Evaluation Result
    # ========================================================

    with open(

        RESULT_PATH,

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            output,

            file,

            ensure_ascii=False,

            indent=2
        )


    # ========================================================
    # 打印最终报告
    # ========================================================

    print()
    print("=" * 70)

    print(
        "Agent Evaluation Summary"
    )

    print("=" * 70)


    print(
        "Total Cases：",
        summary[
            "total_cases"
        ]
    )


    print(
        "Tool Selection Accuracy：",
        (
            summary[
                "tool_selection_accuracy"
            ]
            *
            100
        ),
        "%"
    )


    print(
        "Tool Argument Accuracy：",
        (
            summary[
                "tool_argument_accuracy"
            ]
            *
            100
        ),
        "%"
    )


    print(
        "Task Completion Rate：",
        (
            summary[
                "task_completion_rate"
            ]
            *
            100
        ),
        "%"
    )


    print(
        "Overall Pass Rate：",
        (
            summary[
                "overall_pass_rate"
            ]
            *
            100
        ),
        "%"
    )


    print(
        "Average Latency：",
        summary[
            "average_latency_ms"
        ],
        "ms"
    )


    print()
    print(
        "结果已保存：",
        RESULT_PATH
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )