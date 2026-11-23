# OpsPilot Architecture

## Runtime overview

\`\`\`mermaid
flowchart TD
    Browser[Next.js console] -->|HttpOnly session proxy| API[FastAPI API]
    Service[Application / SDK] -->|JWT or service identity| API
    API --> PG[(PostgreSQL)]
    API -->|Async event task| Redis[(Redis)]
    Redis --> Worker[Celery worker]
    Worker --> PG
    API --> Prom[Prometheus metrics]
    API -->|OTLP traces| Collector[OpenTelemetry Collector]
    Prom --> Grafana[Grafana]
\`\`\`

## Tenant and access model

Each user can belong to one or more organizations through a membership. Access tokens identify a user and selected organization. The API re-reads membership and role from PostgreSQL on each authenticated request, rather than trusting a role embedded in the token. Every event, incident, and service dependency query is scoped to the active organization.

Roles:
- owner: workspace owner and highest access.
- admin: workspace member/role administration and incident operations.
- on_call: event ingestion and incident lifecycle operations.
- viewer: read-only access.

## Event processing

POST /api/v1/events persists events immediately. POST /api/v1/events/async publishes a Celery task to Redis; the worker validates the payload, stores the event, and correlates the incident. Database errors are retried with exponential backoff and jitter. The task uses late acknowledgement so a worker crash does not acknowledge unfinished work.

The event fingerprint includes organization ID, service, event type and normalized message, preventing collisions across organizations while retaining a single unique index.

## Incident intelligence

GET /api/v1/incidents/{id}/analysis uses recent event metadata for the same organization and service. It computes a simple recent event-rate baseline and returns evidence-backed deployment, region and event-pattern hypotheses. Every hypothesis includes a caveat. The result is explicitly not a confirmed root cause.

## Observability

- Prometheus FastAPI Instrumentator exposes request counts and latency at /metrics.
- OpenTelemetry FastAPI tracing is activated when OTEL_EXPORTER_OTLP_ENDPOINT is configured.
- The bundled collector receives OTLP traces and exports them to its debug exporter in the development stack.
- Prometheus scrapes the API and Grafana is provisioned with Prometheus as its default data source.

## Security and known gaps

The Next.js proxy keeps access tokens in an HttpOnly, SameSite=Lax cookie. Production deployment still requires HTTPS, CSRF protections on state-changing browser routes, rate limits, strong secret management and security review. The member-add endpoint links an already registered user; invitation email and password reset are not implemented.
