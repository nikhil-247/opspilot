# OpsPilot

**Enterprise incident management and observability platform.** OpsPilot ingests application events, correlates repeated alerts into incidents, tracks acknowledgement and resolution, and records an auditable incident timeline.

> Status: MVP foundation. The backend event-to-incident workflow is implemented and tested. Authentication, tenant isolation, background queues, telemetry integrations, and the web dashboard are planned milestones, not yet complete features.

## Current capabilities

- FastAPI service with OpenAPI documentation.
- Liveness and database-readiness probes.
- Event ingestion with request validation.
- Persistent event history in PostgreSQL (SQLite is supported for local tests).
- Incident creation for warning, error, and critical events.
- Alert deduplication using a deterministic fingerprint.
- Priority escalation and response-target calculation.
- Incident list filters and pagination.
- Acknowledge, resolve, and reopen lifecycle.
- Incident activity/audit history.
- Automated API tests.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the current data flow, lifecycle, and planned evolution.

## Run locally with Docker

1. Copy `.env.example` to `.env`.
2. Start the database and API:

   ```bash
   docker compose up --build
   ```

3. Open the API docs at [http://localhost:8000/docs](http://localhost:8000/docs).
4. Check readiness at [http://localhost:8000/health/ready](http://localhost:8000/health/ready).

The API container runs Alembic migrations before starting FastAPI.

## Run the backend tests

Python 3.12 or newer is recommended.

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Tests use an isolated in-memory SQLite database and do not require Docker or a running PostgreSQL server.

## Example: ingest an event

```bash
curl -X POST http://localhost:8000/api/v1/events \\
  -H "Content-Type: application/json" \\
  -d '{
    "source": "checkout-api",
    "service": "payment-service",
    "event_type": "database_connection_error",
    "severity": "error",
    "message": "Database connection pool exhausted",
    "attributes": {"region": "ap-south-1", "deployment": "v1.4.2"}
  }'
```

A warning, error, or critical event creates or updates a correlated incident. An informational event is recorded without opening an incident.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Database readiness probe |
| POST | `/api/v1/events` | Ingest an event |
| GET | `/api/v1/events` | List recent events |
| GET | `/api/v1/incidents` | Filter and paginate incidents |
| GET | `/api/v1/incidents/{id}` | Get incident details |
| POST | `/api/v1/incidents/{id}/acknowledge` | Acknowledge an open incident |
| POST | `/api/v1/incidents/{id}/resolve` | Resolve an active incident |
| GET | `/api/v1/incidents/{id}/activity` | Read the incident audit timeline |

## Important production-readiness notes

This repository is an actively developed portfolio project, not a production incident-response service yet. Before production use, it needs tenant isolation, authentication and authorization, rate limiting, secret management, operational monitoring, load testing, and hardened concurrency controls. Never send real customer secrets or sensitive production logs to a development deployment.

## License

MIT. See [LICENSE](LICENSE).
