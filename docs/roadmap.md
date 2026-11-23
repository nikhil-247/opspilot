# OpsPilot Roadmap

## Milestone 1: Incident backend foundation
- [x] FastAPI APIs and OpenAPI docs
- [x] Event ingestion, deduplication and priority escalation
- [x] Incident lifecycle and audit history
- [x] Initial test suite

## Milestone 2: Live console and enterprise access
- [x] Next.js console backed by real API endpoints
- [x] Incident filters, details and activity timeline
- [x] Event explorer and event submission
- [x] JWT authentication and HttpOnly frontend session cookie
- [x] Organization memberships and role checks
- [x] Tenant-scoped incident, event and service dependency queries
- [ ] PostgreSQL migration run against a live container and cross-tenant security review
- [ ] Invite acceptance and password reset lifecycle

## Milestone 3: Background processing and telemetry
- [x] Celery event processing task with retry policy
- [x] Redis broker and Docker worker service
- [x] Prometheus HTTP metrics endpoint and scrape config
- [x] OpenTelemetry FastAPI trace export configuration
- [ ] Queue monitoring, dead-letter handling and load tests
- [ ] Database instrumentation and trace-linked incident views

## Milestone 4: Service topology and incident intelligence
- [x] Tenant-scoped service dependency registry
- [x] Event-rate anomaly signal from recent event windows
- [x] Evidence-backed incident hypotheses from event metadata
- [ ] Automated dependency graph discovery from traces
- [ ] Historical evaluation dataset and calibrated anomaly model
- [ ] Runbook retrieval and evidence-grounded LLM explanation

## Milestone 5: Production hardening
- [ ] CSRF protections and browser security review
- [ ] Rate limiting and service-to-service credentials
- [ ] PostgreSQL concurrency and migration tests
- [ ] Queue failure recovery and idempotency tests
- [ ] Load, integration and browser end-to-end tests
- [ ] Deployment and operations runbooks
