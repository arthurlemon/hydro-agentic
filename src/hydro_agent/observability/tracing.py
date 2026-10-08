"""OpenTelemetry explicite; aucun export cloud activé implicitement."""

import json
import os
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

_provider: TracerProvider | None = None
_propagator = TraceContextTextMapPropagator()


class JsonlExporter(SpanExporter):
    def __init__(self, path: Path) -> None:
        self.path = path

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            for item in spans:
                context = item.context
                assert context is not None
                row = {
                    "name": item.name,
                    "trace_id": f"{context.trace_id:032x}",
                    "span_id": f"{context.span_id:016x}",
                    "parent_span_id": f"{item.parent.span_id:016x}" if item.parent else None,
                    "start_ns": item.start_time,
                    "latency_ms": ((item.end_time or 0) - (item.start_time or 0)) / 1e6,
                    "status": item.status.status_code.name,
                    "attributes": dict(item.attributes or {}),
                }
                # Un seul append par ligne : stdout MCP reste réservé au protocole.
                fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
                try:
                    os.write(fd, (json.dumps(row, ensure_ascii=False) + "\n").encode())
                finally:
                    os.close(fd)
            return SpanExportResult.SUCCESS
        except OSError:
            # Une panne du journal facultatif ne doit pas autoriser ni annuler une action.
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        pass


def configure(path: Path, otlp_endpoint: str = "") -> None:
    global _provider
    if _provider is not None:
        _provider.shutdown()
    _provider = TracerProvider()
    _provider.add_span_processor(SimpleSpanProcessor(JsonlExporter(path)))
    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        _provider.add_span_processor(
            SimpleSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, timeout=5))
        )


def correlation() -> dict[str, str]:
    context = trace.get_current_span().get_span_context()
    return (
        {"trace_id": f"{context.trace_id:032x}", "span_id": f"{context.span_id:016x}"}
        if context.is_valid
        else {}
    )


def carrier() -> dict[str, str]:
    result: dict[str, str] = {}
    _propagator.inject(result)
    return result


@contextmanager
def span(name: str, *, parent: Mapping[str, Any] | None = None, **attributes: Any) -> Iterator[Any]:
    tracer = _provider.get_tracer("hydro-agentic") if _provider else trace.NoOpTracer()
    context = _propagator.extract(dict(parent)) if parent is not None else None
    with tracer.start_as_current_span(
        name,
        context=context,
        attributes=attributes,
        record_exception=False,
        set_status_on_exception=False,
    ) as current:
        try:
            yield current
        except BaseException:
            current.set_status(trace.StatusCode.ERROR)
            raise


def shutdown() -> None:
    if _provider is not None:
        with suppress(Exception):
            _provider.shutdown()
