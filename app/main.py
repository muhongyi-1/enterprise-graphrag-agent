from fastapi import FastAPI

from app.api.chat import (
    router as chat_router
)
import time
import uuid

from fastapi import (
    FastAPI,
    Request,
    Response
)

from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST
)

from app.core.observability import (
    logger,
    push_context,
    pop_context,
    HTTP_REQUESTS,
    HTTP_LATENCY
)

app = FastAPI(
    title="Enterprise GraphRAG Agent",
    description="企业知识库 GraphRAG Agent 平台",
    version="0.1.0"
)

@app.middleware("http")
async def observability_middleware(
        request: Request,
        call_next
):

    request_id = (
        request.headers.get("X-Request-ID")
        or
        str(uuid.uuid4())
    )

    tokens = push_context(
        request_id=request_id
    )

    start_time = time.perf_counter()
    status_code = 500

    logger.info(
        "HTTP request started",
        extra={
            "event":"http_request_started",
            "method":request.method,
            "path":request.url.path
        }
    )

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response

    except Exception:
        logger.exception(
            "HTTP request failed",
            extra={
                "event":"http_request_failed",
                "method":request.method,
                "path":request.url.path
            }
        )
        raise

    finally:
        duration_seconds = time.perf_counter() - start_time
        duration_ms = duration_seconds * 1000

        HTTP_REQUESTS.labels(
            method=request.method,
            path=request.url.path,
            status=str(status_code)
        ).inc()

        HTTP_LATENCY.labels(
            method=request.method,
            path=request.url.path
        ).observe(duration_seconds)

        logger.info(
            "HTTP request finished",
            extra={
                "event":"http_request_finished",
                "method":request.method,
                "path":request.url.path,
                "status":status_code,
                "duration_ms":round(duration_ms, 2)
            }
        )

        pop_context(tokens)

app.include_router(
    chat_router
)

@app.get(
    "/health",
    tags=["System"]
)
async def health():
    return {
        "status":"ok",
        "service":"graphrag-agent"
    }

@app.get(
    "/metrics",
    include_in_schema=False
)
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )