from __future__ import annotations
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace
import structlog

from . import metrics
from .request_context import set_request_id, set_trace_id

log = structlog.get_logger()

class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        request_id = request.headers.get("x-request-id") or f"req-{uuid.uuid4()}"
        set_request_id(request_id)

        # Pull trace id from current span (after OTel instrumentation)
        span = trace.get_current_span()
        span_ctx = span.get_span_context() if span else None
        trace_id = None
        if span_ctx and span_ctx.trace_id:
            trace_id = format(span_ctx.trace_id, "032x")
        set_trace_id(trace_id)

        # Basic request counter
        metrics.http_requests_total.add(1, {
            "method": request.method,
            "path": request.url.path
        })

        try:
            response = await call_next(request)
            return response
        finally:
            dur_ms = (time.time() - start) * 1000.0
            metrics.http_request_duration_ms.record(dur_ms, {
                "method": request.method,
                "path": request.url.path
            })

            # Structured access log
            log.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=getattr(request.state, "status_code", None),
                duration_ms=round(dur_ms, 2),
                request_id=request_id,
                trace_id=trace_id,
                client_host=getattr(request.client, "host", None),
            )
