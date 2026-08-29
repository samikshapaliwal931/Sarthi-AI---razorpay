from __future__ import annotations

import time
import uuid
from typing import Any

import structlog
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from app.config import settings

logger = structlog.get_logger()

tracer = trace.get_tracer("sarthi")


def setup_observability() -> None:
    if not settings.is_production:
        return

    try:
        provider = TracerProvider()
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        logger.info("observability_initialized")
    except Exception as e:
        logger.warning("observability_setup_failed", error=str(e))


def log_event(
    event: str,
    level: str = "info",
    merchant_id: str | None = None,
    correlation_id: str | None = None,
    **kwargs: Any,
) -> None:
    log_fn = getattr(logger, level, logger.info)
    log_fn(
        event,
        merchant_id=merchant_id,
        correlation_id=correlation_id,
        **kwargs,
    )


class Timer:
    def __init__(self, name: str) -> None:
        self.name = name
        self.start_time: float | None = None
        self.duration_ms: int | None = None

    def __enter__(self) -> Timer:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        if self.start_time:
            self.duration_ms = int((time.perf_counter() - self.start_time) * 1000)
            logger.debug("timer_complete", name=self.name, duration_ms=self.duration_ms)
