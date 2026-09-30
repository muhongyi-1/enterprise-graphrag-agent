import asyncio

from app.core.reliability import (
    run_with_retry,
    RetryExhaustedError
)


# ============================================================
# Demo专用 Semaphore
# ============================================================

test_semaphore = (
    asyncio.Semaphore(2)
)


# ============================================================
# 测试1：
#
# 第1、2次失败
# 第3次成功
# ============================================================

attempt_count = 0


async def flaky_task():

    global attempt_count

    attempt_count += 1

    print(
        "flaky_task 当前执行次数：",
        attempt_count
    )

    if attempt_count < 3:

        raise ConnectionError(
            "模拟网络连接失败"
        )

    return "第3次调用成功"


# ============================================================
# 测试2：
#
# 永远很慢，
# 用来测试 Timeout。
# ============================================================

async def slow_task():

    print(
        "slow_task 开始执行"
    )

    await asyncio.sleep(
        2
    )

    return "slow_task成功"


# ============================================================
# Main
# ============================================================

async def main():

    print()
    print("=" * 60)
    print("TEST 1：Retry")
    print("=" * 60)

    result = await run_with_retry(
        operation=flaky_task,
        service_name="FlakyService",
        timeout_seconds=2,
        max_attempts=3,
        base_delay_seconds=0.5,
        retry_exceptions=(ConnectionError, TimeoutError),
        semaphore=test_semaphore
    )

    print("最终结果：", result)

    print()
    print("=" * 60)
    print("TEST 2：Timeout")
    print("=" * 60)

    try:
        await run_with_retry(
            operation=slow_task,
            service_name="SlowService",
            timeout_seconds=0.5,
            max_attempts=2,
            base_delay_seconds=0.5,
            retry_exceptions=(TimeoutError,),
            semaphore=test_semaphore
        )
    except RetryExhaustedError as exc:
        print()
        print("符合预期：所有尝试均失败")
        print(exc)


if __name__ == "__main__":
    asyncio.run(main())