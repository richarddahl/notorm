# Uno Implementation Roadmap

This roadmap captures current strengths of the Uno framework and outlines key improvement areas as actionable tasks.  
Use the checkboxes below to track progress on each implementation task.

---

## 1. What Uno Does Well
- **Domain‑Driven Design first**: Entities, value objects, aggregates, domain events, command bus, unit of work.
- **Modern, flexible DI**: Protocol‑based container, scoped/request lifetimes, auto constructor injection, decorator & discovery registration, FastAPI integration.
- **Async‑First Architecture**: Structured concurrency (TaskGroup), retry/timeouts, enhanced async sessions, proper cancellation support.
- **CQRS & Read Models**: Clear separation of reads vs. writes, dynamic query builders, path/value query routers.
- **PostgreSQL‑Native Power**: JSONB, ULID, row‑level security, vector search (pgvector), graph (AGE) extensions.
- **Rich Peripherals**: Workflow engine, event bus, background jobs, reporting, admin UI scaffold.
- **Error Handling & Observability Foundations**: Centralized error handlers, structlog support, optional middleware.
- **Testability & Dev‑First Tooling**: Hatch envs, pytest/asyncio fixtures, factory_boy, test providers.

---

## 2. Improvement Roadmap
Below are grouped areas of enhancement.  
Check off items as they are implemented or moved to in-progress.

### A) Developer Experience & DDD Scaffolding
- [ ] CLI scaffolding commands (`uno new module`, `uno make entity`, `uno make command/event`)
- [ ] Automatic model→migration code generation (Alembic)
- [ ] Interactive REPL or `uno console` for experimenting with DI and domain models
- [ ] Code‑gen or templating utilities for repetitive patterns (filter handlers, event subscribers)
- [ ] Expanded examples & “cookbook” for common DDD patterns (sagas, aggregates, ACLs)

### B) DevOps & Deployment
- [ ] Official Docker Compose and Kubernetes Helm charts (Postgres, Redis, workers)
- [ ] Zero‑downtime migrations and rolling upgrade support
- [ ] Infrastructure‑as‑Code modules (Terraform/Pulumi) for cloud provisioning
- [ ] OpenTelemetry metrics & tracing integration, health endpoints
- [ ] CI/CD pipeline templates (GitHub Actions, GitLab CI) for test, build, deploy
- [ ] Secret management integrations (Vault, AWS Parameter Store)

### C) End‑User & Administrative UX
- [ ] Polished, composable Admin UI components (CRUD, dashboards, workflows)
- [ ] Theming & branding support for white‑label applications
- [ ] Built‑in multi‑tenant patterns and advanced permissions
- [ ] Optional GraphQL gateway or federated API layer
- [ ] Advanced RBAC & SSO integrations (OAuth2/OIDC, SAML, SCIM)

### D) Documentation & Community Onboarding
- [ ] Interactive tutorials or online playground showcasing DDD & workflows
- [ ] End‑to‑end “Getting Started” guide building a sample DDD app
- [ ] Enhanced API reference generation (mkdocstrings, domain annotations)
- [ ] Cookbooks for common integrations (email, PDF generation, data pipelines)

### E) Production Hardening
- [ ] Blue/green and canary deployment patterns with migration scripts
- [ ] Circuit breakers and health checks for external services
- [ ] Audit trail hooks, PII‑redaction utilities for compliance
- [ ] Performance benchmarking dashboards (Prometheus / Grafana)

---

*This roadmap will evolve as tasks are completed and new priorities emerge.*