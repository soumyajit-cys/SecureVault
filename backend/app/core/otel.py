from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

_initialized = False


def init_otel(app) -> None:
    """
    Enable OpenTelemetry when OTEL_ENABLED is set
    and the instrumentation packages are installed.

    Safe to call unconditionally: without the flag
    (or the dependencies) this is a no-op, so the
    app never hard-depends on the SDK.
    """

    global _initialized

    if _initialized or not settings.OTEL_ENABLED:
        return

    try:

        from opentelemetry import trace
        from opentelemetry.sdk.resources import (
            Resource,
        )
        from opentelemetry.sdk.trace import (
            TracerProvider,
        )
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
        )

        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        from opentelemetry.instrumentation.fastapi import (
            FastAPIInstrumentor,
        )

    except ImportError as exc:
        logger.warning(
            "otel_dependencies_missing",
            error=str(exc),
        )
        return

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": (
                    f"securevault-{settings.APP_ENV}"
                ),
            }
        )
    )

    endpoint = (
        settings.OTEL_EXPORTER_OTLP_ENDPOINT
        or "http://localhost:4318"
    )

    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=endpoint
            )
        )
    )

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(
        app
    )

    _initialized = True

    logger.info(
        "otel_enabled",
        endpoint=endpoint,
    )
