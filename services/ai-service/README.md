# AI Service — MacroCrypto AI

## Overview

The AI Service (ML service) generates Bitcoin price predictions using Prophet, XGBoost, and LightGBM, driven by macro and market features prepared by the data service.

## Architecture Context

| Service | Responsibility |
|---------|----------------|
| **data-service** | Collects BTC and macro data; publishes events; writes the 50-feature training set |
| **AI Service** (this) | Trains models, serves predictions, publishes `PredictionGenerated` |
| **api-gateway** | External REST entry point (proxies prediction routes) |
| **alert-service** | Consumes predictions and price events for notifications |

## Quick Start (Docker — recommended)

Graders and new teammates should start from the **repository root**, not this folder.

### Prerequisites

- Docker Desktop running
- `make` (macOS/Linux)

### 1. Env file

```bash
cp services/ai-service/.env.example services/ai-service/.env
```

No edits are required for Compose: defaults use service names (`postgres`, `redis`, `rabbitmq`, `mlflow`) and `SHARED_DATA_DIR=/app/shared/features`.

Also copy env files for the other Compose services if you have not already (see [services/README.md](../README.md#quick-start)).

### 2. Start infrastructure + ML stack

**Full backend** (simplest — everything the dashboard needs):

```bash
make up
make ps
```

That starts Postgres, Redis, RabbitMQ, MLflow, **data-service**, **ai-service**, **alert-service**, and **api-gateway**.

**AI service only** (after infra is already up, or Compose will start dependencies):

```bash
make ai-up
```

Compose pulls in Postgres, Redis, RabbitMQ, and MLflow automatically via `depends_on`. It does **not** start data-service; see [Relationship to data-service](#relationship-to-data-service).

### 3. Verify

```bash
make ai-health          # http://localhost:8002/health
make ai-ready           # readiness (models / feature source)
```

| Check | URL |
|-------|-----|
| OpenAPI docs | http://localhost:8002/docs |
| Health | http://localhost:8002/health |
| MLflow UI | http://localhost:5000 |

From the host:

```bash
curl -s http://localhost:8002/health | jq
```

Predictions exposed to the UI go through the gateway: http://localhost:8000/docs (after `make up` or `make api-up`).

### Using Make commands

Run from the repository root:

| Command | Purpose |
|---------|---------|
| `make ai-up` / `make ai-down` | Start / stop ai-service (rebuild on up) |
| `make ai-logs` | Tail logs |
| `make ai-restart` | Restart container |
| `make ai-shell` | Shell inside container |
| `make ai-test` | Pytest inside container |
| `make ai-health` / `make ai-ready` | HTTP checks |
| `make mlflow-ui` | Open MLflow in browser |

## Relationship to data-service

| Need | Start data-service? |
|------|---------------------|
| Service boots, `/health`, API docs | **No** — ai-service only needs Postgres, Redis, RabbitMQ, MLflow |
| **Parquet feature files** (default `FEATURE_SOURCE=parquet`) | **No separate step** — Compose mounts `services/data-service/app/data/processed` read-only into the ai-service container |
| Live price / macro ingestion, RabbitMQ `PriceUpdated` / `IndicatorUpdated`, refreshing features in DB | **Yes** — `make data-up` or full `make up` |
| Frontend predictions via gateway | **Yes** for gateway — use `make up` or at least `make api-up` + `make ai-up` + `make data-up` |

For a grader running the **whole product**, use `make up` once; that covers data-service and ai-service together.

## Local development (without Docker)

Use this when debugging Python code in the ai-service tree. Infrastructure should still be reachable (typically via `docker compose up -d postgres redis rabbitmq mlflow` from the repo root).

```bash
cd services/ai-service
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Point `.env` at localhost for dependencies, for example:

```dotenv
DATABASE_URL=postgresql://macro:crypto@localhost:5432/macrocrypto
REDIS_HOST=localhost
RABBITMQ_HOST=localhost
MLFLOW_TRACKING_URI=http://localhost:5000
SHARED_DATA_DIR=../data-service/app/data/processed
```

From the repository root:

```bash
make ai-venv
make ai-install
make ai-run          # uvicorn on port 8002 with reload
```

## Responsibilities

- Consume `PriceUpdated` and `IndicatorUpdated` events from RabbitMQ
- Engineer features and train/retrain model versions
- Serve 24-hour and 7-day predictions with confidence intervals
- Publish `PredictionGenerated` events
- Track metrics (MAE, RMSE, MAPE) and register models in MLflow
- Cache predictions in Redis

## Events

### Consumed

| Event | Source |
|-------|--------|
| `PriceUpdated` | data-service |
| `IndicatorUpdated` | data-service |

### Produced

| Event | Consumer |
|-------|----------|
| `PredictionGenerated` | alert-service, api-gateway |

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.13 |
| Web Framework | FastAPI |
| ML Models | Prophet, XGBoost, LightGBM |
| Model Registry | MLflow |
| Database | TimescaleDB |
| Cache | Redis |
| Message Broker | RabbitMQ |
| Scheduling | APScheduler |

## Related documentation

- [Backend runbook (all services)](../README.md)
- [Root README — Run locally](../../README.md#run-locally)
- [Microservices design](../../docs/design/microservices.md)
