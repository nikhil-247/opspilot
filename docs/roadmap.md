# Development Roadmap

## Milestone 1: Backend event-to-incident workflow (current)

- [x] FastAPI application and API documentation
- [x] PostgreSQL-ready SQLAlchemy models
- [x] Alembic initial schema migration
- [x] Event ingestion and validation
- [x] Fingerprint-based incident deduplication
- [x] Priority escalation and SLA response targets
- [x] Incident acknowledge/resolve/reopen lifecycle
- [x] Activity/audit trail
- [x] Automated API tests
- [x] Docker Compose development environment
- [x] GitHub Actions CI workflow

## Milestone 2: Real dashboard and demo workflow

- [ ] Next.js + TypeScript console
- [ ] Typed API client and loading/error/empty states
- [ ] Live incident list and filters
- [ ] Incident details and activity timeline
- [ ] Event simulator connected to the backend
- [ ] Browser end-to-end tests

## Milestone 3: Enterprise access controls

- [ ] Authentication
- [ ] Tenant and organization data model
- [ ] Role-based authorization
- [ ] Tenant isolation tests
- [ ] Rate limiting and secure configuration

## Milestone 4: Observability and asynchronous processing

- [ ] Background event processing
- [ ] Durable queue and retry/dead-letter policy
- [ ] OpenTelemetry instrumentation
- [ ] Prometheus metrics and Grafana dashboards
- [ ] Service dependency graph

## Milestone 5: Intelligent incident assistance

- [ ] Evidence retrieval from related events and deployments
- [ ] Statistical anomaly detection
- [ ] Root-cause hypotheses with evidence and confidence
- [ ] Runbook recommendations
- [ ] Evaluation dataset and quality measurements
