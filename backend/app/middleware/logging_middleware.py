"""
Request/Response logging middleware.

Logs every incoming HTTP request and its response with:
    - A unique request ID (X-Request-ID header, generated if not provided)
    - HTTP method, path, status code
    - Response time in milliseconds
    - Caller IP address

The request ID is injected into the response headers so clients can
correlate their requests with backend logs.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that logs all HTTP requests and responses.

    Assigns a unique X-Request-ID to each request for distributed tracing.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or reuse request ID from headers
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        # Store request ID in request state for downstream access
        request.state.request_id = request_id

        # Record start time
        start_time = time.perf_counter()

        # Log incoming request
        logger.info(
            "→ %s %s | request_id=%s | ip=%s",
            request.method,
            request.url.path,
            request_id,
            request.client.host if request.client else "unknown",
        )

        # Process the request
        response: Response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Inject request ID into response headers for client correlation
        response.headers["X-Request-ID"] = request_id

        # Log response
        log_fn = logger.warning if response.status_code >= 400 else logger.info
        log_fn(
            "← %s %s | status=%d | duration=%.2fms | request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )

        return response
