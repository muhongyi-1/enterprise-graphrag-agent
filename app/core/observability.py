import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone

from prometheus_client import (
    Counter,
    Histogram
)

request_id_var = ContextVar(
    "request_id",
    default="-"
)

user_id_var = ContextVar(
    "user_id",
    default="-"
)

thread_id_var = ContextVar(
    "thread_id",
    default="-"
)

def push_context(
        request_id: str | None = None,
        user_id: str | None = None,
        thread_id: str | None = None
):
    tokens = []

    if request_id is not None:
        tokens.append(
            (
                request_id_var,
                request_id_var.set(request_id)
            )
        )

    if user_id is not None:
        tokens.append(
            (
                user_id_var,
                user_id_var.set(user_id)
            )
        )

    if thread_id is not None:
        tokens.append(
            (
                thread_id_var,
                thread_id_var.set(thread_id)
            )
        )

    return tokens

def pop_context(tokens):
    for var, token in reversed(tokens):
        var.reset(token)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),
            "level":
                record.levelname,
            "logger":
                record.name,
            "message":
                record.getMessage(),
            "request_id":
                request_id_var.get(),
            "user_id":
                user_id_var.get(),
            "thread_id":
                thread_id_var.get()
        }

        optional_fields = [
            "event",
            "duration_ms",
            "tool_name",
            "status",
            "attempt",
            "error_type",
            "method",
            "path",
            "tool_calls_count"
        ]

        for field in optional_fields:
            value = getattr(
                record,
                field,
                None
            )

            if value is not None:
                data[field] = value

        if record.exc_info:
            data["exception"] = (
                self.formatException(
                    record.exc_info
                )
            )

        return json.dumps(
            data,
            ensure_ascii=False
        )

logger = logging.getLogger(
    "graphrag_agent"
)

logger.setLevel(
    logging.INFO
)

if not logger.handlers:
    handler = (
        logging.StreamHandler()
    )

    handler.setFormatter(
        JsonFormatter()
    )

    logger.addHandler(
        handler
    )

logger.propagate = False

HTTP_REQUESTS = Counter(
    "agent_http_requests_total",
    "Total number of HTTP requests",
    [
        "method",
        "path",
        "status"
    ]
)

HTTP_LATENCY = Histogram(
    "agent_http_request_duration_seconds",
    "HTTP request latency",
    [
        "method",
        "path"
    ]
)

LLM_CALLS = Counter(
    "agent_llm_calls_total",
    "Total number of LLM calls",
    [
        "status"
    ]
)

LLM_LATENCY = Histogram(
    "agent_llm_call_duration_seconds",
    "LLM call latency"
)

TOOL_CALLS = Counter(
    "agent_tool_calls_total",
    "Total number of tool calls",
    [
        "tool_name",
        "status"
    ]
)

TOOL_LATENCY = Histogram(
    "agent_tool_call_duration_seconds",
    "Tool call latency",
    [
        "tool_name"
    ]
)
