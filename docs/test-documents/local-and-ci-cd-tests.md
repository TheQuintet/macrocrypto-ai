# Local and CI Testing

This guide describes the test types in the repository and the checks run by
[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).

> **AI disclosure:** AI use on this document is recorded as `Co-authored-by` trailers on its commits. See [AI-assisted development disclosure](../ai-assisted-development-disclosure.md#how-ai-use-is-recorded).

## Test categories

- **Unit tests** exercise an isolated function, component, or module without
  requiring the full application stack. Frontend unit tests use Vitest under
  `frontend/src`; backend pytest suites include tests marked `unit`.
- **Backend integration tests** exercise interactions with dependencies such as
  PostgreSQL, Redis, and RabbitMQ. Backend pytest suites use the `integration`
  marker for these tests; the exact dependencies vary by service.
- **Backend E2E tests** use the pytest `e2e` marker for full-flow tests within
  the relevant service test suite.
- **Frontend UI integration tests** use Playwright in
  `frontend/e2e/ui-integration/`. They exercise browser flows against the
  frontend, usually with simulated frontend data; they do not by themselves
  validate backend services.
- **Frontend system E2E tests** use Playwright in `frontend/e2e/system/` (the
  `e2e` project). They drive the real Vite app against a **reachable API
  gateway** and backing services (live HTTP/WebSocket data, not mocked in the
  browser). Specs **skip** when the gateway is down so local runs without
  Compose do not fail.
- **System stack job** starts selected services with Docker Compose, verifies
  cross-service Gateway routes with `curl`, then runs the **system E2E**
  Playwright suite against the live stack. It is a focused smoke check, not
  exhaustive coverage of every endpoint or workflow.
- **Quality and security checks** are separate from behavioral tests:
  ESLint, TypeScript typechecking, Python lint/format checks, and `pip-audit`
  inspect code or dependencies rather than exercise user journeys.

## Local testing

### Frontend

Run commands from `frontend/` to install dependencies, lint and typecheck the
application, run the Vitest unit suite, and run the Playwright UI integration
suite:

```bash
npm ci
npm run lint
npm run typecheck
npm test
npx playwright install chromium
npm run test:ui-integration
```

Playwright also has commands for the **system E2E** project and for running
both browser projects:

```bash
npm run test:e2e:system
npm run test:e2e
```

**System E2E locally** (gateway on port **8000**, e.g. `docker compose up` for
postgres, redis, data-service, alert-service, api-gateway):

```bash
VITE_API_GATEWAY_BASE_URL=http://127.0.0.1:8000 npm run test:e2e:system
```

`playwright.config.ts` forwards `VITE_API_GATEWAY_BASE_URL` into the Vite dev
server so the app hits the gateway during E2E runs. See
[`frontend/e2e/system/README.md`](../../frontend/e2e/system/README.md) for
spec inventory and the UI-integration vs system split.

| Spec | What it checks |
|------|----------------|
| `app.smoke.spec.ts` | Dashboard loads with live BTC price from the gateway |
| `routing.spec.ts` | Sidebar navigation to macro, forecasts, and calendar |
| `alerts.spec.ts` | Alerts page loads price, macro, and prediction tabs via gateway |

Shared helpers: `gateway.specHelpers.ts` (gateway health + skip), co-located
`*.specHelpers.ts` per spec; routing/price helpers are reused from
`e2e/ui-integration/` where flows overlap.

To run only the **UI integration** dashboard smoke (simulated data, no stack):

```bash
npm run test:ui-integration -- e2e/ui-integration/app.smoke.spec.ts
```

### Backend services

The API Gateway, Alert Service, and Data Service each have pytest suites and
register `unit`, `integration`, `e2e`, and `slow` markers. Running `pytest`
executes the discovered suite, including tests across the applicable
categories. From the repository root:

```bash
(cd services/api-gateway && pytest)
(cd services/alert-service && pytest)
(cd services/data-service && pytest)
```

Provide the service's required infrastructure and environment configuration
when running locally. In CI, the Data Service suite excludes `tests/ml_qa` and
uses PostgreSQL, Redis, and RabbitMQ.

## GitHub Actions CI

CI detects changed paths and runs relevant jobs. A manual `workflow_dispatch`
can set `run-everything` to run the path-filtered checks across the repository.

| Job | What it checks | When it runs |
|---|---|---|
| Frontend | ESLint, TypeScript typecheck, and Vitest unit tests | Frontend or CI workflow changes |
| Frontend UI integration | Dashboard smoke spec in Chromium using simulated frontend data (no Compose) | Frontend or CI workflow changes |
| API Gateway | Gateway pytest suite with TimescaleDB PostgreSQL; coverage shown in the job summary | API Gateway or CI workflow changes, or manual run-everything |
| Alert Service | Alert Service pytest suite with TimescaleDB PostgreSQL; coverage shown in the job summary | Alert Service or CI workflow changes, or manual run-everything |
| Data Service | Starts PostgreSQL, Redis, and RabbitMQ; starts the FastAPI app; runs pytest (excluding `tests/ml_qa`); coverage shown in the job summary | Data Service or CI workflow changes, or manual run-everything |
| Python quality | Flake8 checks on changed Python files; Black formatting is advisory | Changed Python files |
| Security Audit | `pip-audit` for API Gateway, Alert Service, and Data Service requirements | After its backend test job dependencies succeed |
| System stack | Starts infrastructure and selected backend services in Docker Compose, verifies Gateway routes with `curl`, then runs **`npm run test:e2e:system`** (Playwright system E2E against the live gateway) | Frontend, selected backend service, shared, infrastructure, Compose, or CI workflow changes |

Coverage is reported separately for API Gateway, Alert Service, and Data
Service in their respective GitHub Actions job summaries. There is no enforced
coverage percentage threshold. AI Service is not included in these CI coverage
summaries.

## System stack smoke and health endpoints

All four services (API Gateway, Alert Service, Data Service, and AI Service)
implement a `/health` endpoint. AI Service additionally implements
`/health/live` and `/health/ready`. The existence of these endpoints does not
mean every dependency is necessarily healthy.

The system stack job does not use `/health` for its readiness checks. It
verifies the relevant OpenAPI documents and makes actual routed requests: the
Gateway must return a populated BTC price from Data Service and a notifications
response from Alert Service. After that, Playwright **system E2E** specs assert
that the dashboard, navigation, and alerts UI work through the live gateway
(with `VITE_API_GATEWAY_BASE_URL=http://127.0.0.1:8000`).

The stack job exercises the API Gateway, Data Service, Alert Service,
PostgreSQL, Redis, and RabbitMQ. To avoid external Binance availability, CI
generates a temporary Binance-compatible feed with deterministic historical
candles and WebSocket ticker updates. AI Service and MLflow are not started or
tested by this job; an empty AI environment-file placeholder is created only
because the shared Compose configuration references that file. The Compose
file itself is not modified by this CI job.

The `system-stack-smoke` job has been confirmed passing in GitHub Actions.

The CD workflow builds and pushes container images to the live server.
