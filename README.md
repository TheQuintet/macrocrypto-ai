# MacroCrypto AI

**AI-powered Bitcoin intelligence driven by macroeconomic data.**

Quantic MSSE capstone (cohort November 2026). GitHub repository for [TheQuintet/macrocrypto-ai](https://github.com/TheQuintet/macrocrypto-ai).

Traders and analysts today split Bitcoin prices (CoinGecko, TradingView) from macroeconomic series (FRED). This platform puts **BTC market data, macro indicators, forecasts, and alerts** in one dashboard so users can see *why* price is moving, not only *what* it is.

| Persona | Need |
|---------|------|
| **BTC Trader** | Fast 24-hour and 7-day price, macros, and alerts |
| **Investment Analyst** | Historical and indicator views they can check against official sources |

Full problem, scope, and personas: [docs/project-scope.md](./docs/project-scope.md) · [docs/user-personas.md](./docs/user-personas.md).

Program rules and the five mandatory deliverables: [docs/quantic/README.md](./docs/quantic/README.md).

---

## Contents

- [Team](#team)
- [Architecture](#architecture)
- [Repository layout](#repository-layout)
- [Run locally](#run-locally)
- [Test](#test)
- [Deploy](#deploy)
- [Agile process](#agile-process)
- [Design and testing documentation](#design-and-testing-documentation)
- [Documentation map](#documentation-map)
- [Contributing](#contributing)

---

## Team

Capstone requires a named **Product Owner** and **Scrum Master**. Current assignments:

| Member | Capstone / primary role |
|--------|-------------------------|
| Sid Ahmed Mahieddine | **Product Owner** |
| Loredana Lungu | **Scrum Master** (frontend) |
| Mael Taye Deneke | **Code Owner** (backend) |
| Kingson Emma-Ochu | Frontend |
| Richard Owusu (Ph.D.) | Frontend and ML |

Contacts, timezones, and availability: [docs/team-roles.md](./docs/team-roles.md).

---

## Architecture

Event-driven microservices. Collectors publish on **RabbitMQ**; services store history in **TimescaleDB (Postgres)** and cache in **Redis**. The dashboard is a separate React app. We chose this so data ingestion, forecasting, and alerts can scale independently — [ADR-003](./docs/design/adr/ADR-003-event-driven-architecture.md), [ADR-001](./docs/design/adr/ADR-001-use-rabbitmq.md).

| Piece | Role |
|-------|------|
| **Frontend** | Vite + React dashboard (TypeScript, Tailwind, ShadCN, Zustand, TanStack Query) |
| **data-service** | BTC (Binance) and macro (FRED) collection; HTTP APIs |
| **alert-service** | Alert rules and notifications |
| **ai-service** | BTC price forecasting (Prophet, XGBoost, LightGBM) |
| **api-gateway** | External REST entry point (proxies data-service and alert-service) |
| **Postgres / Redis / RabbitMQ / MLflow** | Persistence, cache, events, model registry |

Which containers Compose starts today, ports, and endpoints: [services/README.md](./services/README.md#services). Diagrams and service boundaries: [C4 model](./docs/design/c4-model.md) · [microservices](./docs/design/microservices.md).

---

## Repository layout

```
macrocrypto-ai/
├── Makefile                 # Backend Compose commands (run from this folder)
├── docker-compose.yml
├── frontend/                # Dashboard
├── services/                # data-service, alert-service, ai-service, api-gateway
├── shared/                  # Shared backend code
├── infrastructure/          # Supporting scripts (for example DB init)
├── docs/                    # Scope, design, Agile, Quantic
├── GITHUB_FLOW.md
└── CONTRIBUTING.md
```

---

## Run locally

A grader (or new teammate) should be able to clone, start the backend, and open the UI from this section. Prerequisites: **Docker Desktop** running, **make**, **Node.js 20+** and **npm**.

### Backend

In the repository root:

```bash
cp services/data-service/.env.example services/data-service/.env
cp services/alert-service/.env.example services/alert-service/.env
cp services/ai-service/.env.example services/ai-service/.env
cp services/api-gateway/.env.example services/api-gateway/.env
make up
make ps
```

`make up` starts infrastructure (including MLflow), **data-service**, **alert-service**, **ai-service**, and **api-gateway**. To start (or rebuild) one of those after the rest is already up:

```bash
make ai-up
make api-up
```

| Service | Docs | Health |
|---------|------|--------|
| API Gateway | http://localhost:8000/docs | http://localhost:8000/health |
| Data service | http://localhost:8001/docs | http://localhost:8001/health |
| AI service | http://localhost:8002/docs | http://localhost:8002/health |
| Alert service | http://localhost:8003/docs | http://localhost:8003/health |

Env files, commands, and troubleshooting: [services/README.md — Quick start](./services/README.md#quick-start) · [ai-service README](./services/ai-service/README.md) · [api-gateway README](./services/api-gateway/README.md).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Scripts and stack: [frontend/README.md](./frontend/README.md).

### Connect UI to live APIs

Point the dashboard at the **API Gateway** (port 8000), not at the services behind it. After the backend is up, from `frontend/`:

```bash
cp .env.example .env.local
```

Set:

```dotenv
VITE_API_GATEWAY_BASE_URL=http://localhost:8000
```

Restart the Vite server so it picks up the variable. Leave the value empty for a frontend-only run with simulated data. Steps: [Connect to the API Gateway](./frontend/README.md#connect-to-the-api-gateway).

---

## Test

Capstone scoring rewards automated tests that a grader can run.

**Frontend** (from `frontend/`):

```bash
npm test                      # Vitest unit tests
npm run test:ui-integration   # Playwright UI integration
```

**Backend** (from the repository root, with Compose up):

```bash
make data-test                # data-service pytest
make alert-test               # alert-service pytest
make ai-test                  # ai-service pytest
```

What we test and why: [frontend/README.md](./frontend/README.md) (unit / UI integration / E2E split) and the [design and testing](#design-and-testing-documentation) docs below.

---

## Deploy

A **publicly accessible** app is a mandatory deliverable. The live URL and platform are recorded in [docs/quantic/deliverables.md](./docs/quantic/deliverables.md#2-deployed-application) (update that page when the URL exists — not this README).

Secrets stay in environment variables; do not commit `.env` files.

---

## Agile process

We follow Agile with **at least three sprints**, GitHub Issues, and Project boards. Work that is not on a board is not tracked.

```
PLAN → ASSIGN → WORK → REVIEW → TRACK → CLOSE → RETROSPECT
```

| Ceremony | How we run it | Details |
|----------|----------------|---------|
| Planning | Select stories, estimate, assign owners | [Sprint planning](./docs/project-workflow.md#sprint-planning) |
| Refinement | Clarify acceptance criteria before the sprint | [Backlog refinement](./docs/project-workflow.md#backlog-refinement) |
| Daily standup | Async in Slack | [Daily standup](./docs/project-workflow.md#daily-standup) |
| Review | Offline — pull `main` and use the app | [Sprint review](./docs/project-workflow.md#sprint-review) |
| Retrospective | What went well / what to improve | [Retrospective](./docs/project-workflow.md#retrospective) |
| Delivery | Branch from `main`, PR, review, merge | [GitHub Flow](./GITHUB_FLOW.md) |

---

## Design and testing documentation

The written design-and-testing deliverable must be **manual** (no pasted AI prose). Architecture, patterns, ADRs, and testing approach live under `docs/design/`:

| Document | What it covers |
|----------|----------------|
| [Design plan](./docs/design/README.md) | What we produce and skip for MVP |
| [C4 model](./docs/design/c4-model.md) | Context and containers |
| [Microservices](./docs/design/microservices.md) | Boundaries, data, events |
| [Event-driven architecture](./docs/design/event-driven-architecture.md) | Broker and flows |
| [API design](./docs/design/api-design.md) | HTTP surface |
| [ADRs](./docs/design/adr/README.md) | Why RabbitMQ, FastAPI, Prophet, database-per-service |
| [Non-functional requirements](./docs/design/non-functional-requirements.md) | Performance, availability, security |

Submission status for that deliverable: [docs/quantic/deliverables.md](./docs/quantic/deliverables.md#3-design-and-testing-document).

---

## Documentation map

Add or rename long-form docs via [docs/README.md](./docs/README.md), not by expanding this file.

| Need | Page |
|------|------|
| Product scope and personas | [docs/project-scope.md](./docs/project-scope.md) · [docs/user-personas.md](./docs/user-personas.md) |
| Backend runbook | [services/README.md](./services/README.md) |
| Frontend runbook | [frontend/README.md](./frontend/README.md) |
| Team and sprints | [docs/team-roles.md](./docs/team-roles.md) · [docs/project-workflow.md](./docs/project-workflow.md) |
| Capstone grading and policies | [docs/quantic/grading.md](./docs/quantic/grading.md) · [docs/quantic/policies.md](./docs/quantic/policies.md) |

---

## Contributing

Branch from `main`, open a pull request, request review. [CONTRIBUTING.md](./CONTRIBUTING.md) · [GITHUB_FLOW.md](./GITHUB_FLOW.md).

This project is proprietary — [LICENSE.md](./LICENSE.md).
