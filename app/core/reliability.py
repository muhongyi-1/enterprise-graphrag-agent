import asyncio

from collections.abc import (
    Awaitable,
    Callable
)

from typing import (
    TypeVar
)

from openai import (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError
)

from app.core.observability import (
    logger
)

T = TypeVar("T")

class RetryExhaustedError(
    RuntimeError
):
    pass

LLM_RETRYABLE_EXCEPTIONS = (
    TimeoutError,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError
)

llm_semaphore = asyncio.Semaphore(5)
tool_semaphore = asyncio.Semaphore(10)

async def run_with_retry(
        operation: Callable[
            [],
            Awaitable[T]
        ],
        *,
        service_name: str,
        timeout_seconds: float,
        max_attempts: int,
        base_delay_seconds: float,
        retry_exceptions: tuple,
        semaphore: asyncio.Semaphore
) -> T:
    last_exception = None

    for attempt in range(
        1,
        max_attempts + 1
    ):
        try:
            logger.info(
                f"{service_name} call started",
                extra={
                    "event": "dependency_call_started",
                    "attempt": attempt
                }
            )

            async with semaphore:
                result = await asyncio.wait_for(
                    operation(),
                    timeout=timeout_seconds
                )

            logger.info(
                f"{service_name} call succeeded",
                extra={
                    "event": "dependency_call_succeeded",
                    "attempt": attempt,
                    "status": "success"
                }
            )

            return result

        except retry_exceptions as exc:
            last_exception = exc

            logger.warning(
                f"{service_name} call failed",
                extra={
                    "event": "dependency_call_failed",
                    "attempt": attempt,
                    "status": "failed",
                    "error_type": type(exc).__name__
                }
            )

            if attempt == max_attempts:
                break

            delay = (
                base_delay_seconds
                *
                (
                    2
                    **
                    (
                        attempt - 1
                    )
                )
            )

            logger.warning(
                (
                    f"{service_name} will retry "
                    f"after {delay:.2f}s"
                ),
                extra={
                    "event": "dependency_retry",
                    "attempt": attempt,
                    "error_type": type(exc).__name__
                }
            )

            await asyncio.sleep(delay)

    logger.error(
        f"{service_name} exhausted all retry attempts",
        extra={
            "event": "dependency_retry_exhausted",
            "attempt": max_attempts,
            "status": "failed",
            "error_type": (
                type(last_exception).__name__
                if last_exception
                else "UnknownError"
            )
        }
    )

    raise RetryExhaustedError(
        f"{service_name} 在 {max_attempts} 次尝试后仍然失败"
    ) from last_exception
