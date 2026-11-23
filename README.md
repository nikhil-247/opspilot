# OpsPilot

**OpsPilot is an enterprise incident management and observability platform.** It ingests application events, groups correlated failures into incidents, tracks response workflows, and provides evidence-backed operational analysis.

## Current capabilities

- FastAPI backend with OpenAPI docs.
- JWT authentication and organization-scoped memberships.
- Owner, admin, on-call and viewer roles.
- Tenant-scoped events, incidents, activity history and service dependencies.
- Event deduplication, priority escalation and SLA response targets.
- Incident acknowledge, resolve and reopen lifecycle.
- Celery + Redis asynchronous event ingestion.
- Evidence-based incident hypotheses and event-rate anomaly signals.
- Prometheus HTTP metrics and optional OpenTelemetry trace export.
- Next.js console with a 15-second auto-refreshing incident queue, filtered event explorer, incident details, team access and service dependency registry.
- Docker Compose stack for PostgreSQL, Redis, API, worker, frontend, OpenTelemetry Collector, Prometheus and Grafana with a provisioned API overview dashboard.

## Run the complete stack

1. Copy \`.env.example\` to \`.env\`.
2. Replace \`SECRET_KEY\` with a long random value before sharing the deployment.
3. Start all services:

   \`\`\`bash
   docker compose up --build
   \`\`\`

4. Open the console at http://localhost:3000 and create a workspace.
5. Open API docs at http://localhost:8000/docs.
6. Open Prometheus at http://localhost:9090, Grafana at http://localhost:3001, and metrics at http://localhost:8000/metrics. Grafana's OpsPilot API Overview dashboard is provisioned automatically.

Local-only Grafana defaults are user admin, password opspilot_dev. Change these before any shared deployment.

## Backend tests

\`\`\`bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
\`\`\`

Tests use an isolated SQLite database. CI separately validates Alembic migrations against a fresh SQLite database.

## Frontend development

\`\`\`bash
cd frontend
npm install
npm run dev
\`\`\`

By default, the same-origin Next.js proxy calls the API at http://127.0.0.1:8000. Set API_URL to override it.

See [docs/architecture.md](docs/architecture.md) and [docs/roadmap.md](docs/roadmap.md).

## Production readiness

This is an engineering portfolio project, not yet a production-ready paging system. Before internet-facing use, add a managed secret store, HTTPS, CSRF protection for browser mutations, rate limiting, hardened invite and identity verification, tenant isolation tests against PostgreSQL, queue failure/dead-letter dashboards, load testing, and security review. The anomaly analysis is deterministic and labels hypotheses as unconfirmed; it is not a validated RCA model.
