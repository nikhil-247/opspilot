from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app.api.router import api_router
from app.core.config import settings

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests processed by the OpsPilot API.",
    ["method", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method"],
)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Tenant-aware incident management API for ingesting events, correlating alerts, "
        "and tracking incident response."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.middleware("http")
async def collect_http_metrics(request: Request, call_next):
    started_at = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        REQUEST_COUNT.labels(method=request.method, status_code="500").inc()
        REQUEST_LATENCY.labels(method=request.method).observe(perf_counter() - started_at)
        raise

    REQUEST_COUNT.labels(
        method=request.method, status_code=str(response.status_code)
    ).inc()
    REQUEST_LATENCY.labels(method=request.method).observe(perf_counter() - started_at)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(api_router)


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if settings.otel_exporter_otlp_endpoint:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    from app.db.session import engine

    provider = TracerProvider(resource=Resource.create({"service.name": settings.otel_service_name}))
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        )
    )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {"name": settings.app_name, "version": settings.app_version, "docs": "/docs"}
