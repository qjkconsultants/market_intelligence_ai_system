from __future__ import annotations
from opentelemetry import metrics

_meter = metrics.get_meter("doc-ingestion")

http_requests_total = _meter.create_counter(
    name="http_requests_total",
    description="Total HTTP requests",
    unit="1"
)

http_request_duration_ms = _meter.create_histogram(
    name="http_request_duration_ms",
    description="HTTP request duration in milliseconds",
    unit="ms"
)

uploads_initiated_total = _meter.create_counter(
    name="uploads_initiated_total",
    description="Total upload init calls",
    unit="1"
)

uploads_completed_total = _meter.create_counter(
    name="uploads_completed_total",
    description="Total upload complete calls",
    unit="1"
)
