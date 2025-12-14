from __future__ import annotations

import logging
import os
import sys
import structlog
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

def configure_structured_logging(service_name: str, log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Standard logging setup
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    root.setLevel(level)
    root.addHandler(handler)

    # Structlog setup for JSON logs
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Ensure stdlib logs are also structured-ish
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)

def configure_opentelemetry(service_name: str) -> None:
    # Resource describes this service in traces/metrics
    resource = Resource.create({
        "service.name": service_name,
        "service.namespace": os.getenv("SERVICE_NAMESPACE", "doc-platform"),
        "deployment.environment": os.getenv("APP_ENV", "local"),
    })

    # Tracing
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter()  # endpoint is read from OTEL_EXPORTER_OTLP_ENDPOINT
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Metrics
    metric_exporter = OTLPMetricExporter()
    reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)

    # Auto-instrumentation
    RequestsInstrumentor().instrument()
    URLLib3Instrumentor().instrument()
    LoggingInstrumentor().instrument(set_logging_format=False)

def instrument_fastapi(app) -> None:
    FastAPIInstrumentor.instrument_app(app)
