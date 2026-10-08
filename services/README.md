# MacroCrypto AI — Services (Backend)

Backend microservices and the infrastructure they depend on, run through Docker Compose from the repository root.

**`make up`** starts four infrastructure containers (Postgres/TimescaleDB, Redis, RabbitMQ, MLflow) and four application services (api-gateway, data-service, ai-service, alert-service). See [Services](#services).

## Prerequisites

- **Docker Desktop**, installed *and running*. `docker info` errors if it is installed but not started.
- `make` (preinstalled on macOS and Linux).
- `jq`, optional — only `make health`, `make price` and `make watch-price` use it.

## Quick start

### 1. Create the service env files

```bash
cp services/data-service/.env.example services/data-service/.env
cp services/alert-service/.env.example services/alert-service/.env
cp services/ai-service/.env.example services/ai-service/.env
cp services/api-gateway/.env.example services/api-gateway/.env
```

**Required.** `docker-compose.yml` declares `env_file` for all four microservices, so Compose needs these files. They are gitignored and are not in a fresh clone.

No edits needed for a first run. The defaults use Compose service names (`postgres`, `redis`, `rabbitmq`, `mlflow`) rather than `localhost`, which is what the containers need.

### 2. Start

In the repository root:

```bash
make up
```

The first run takes a few minutes — it builds the service images and pulls the infrastructure images. Later starts take seconds.

Microservices wait on healthy infrastructure: **ai-service** also waits for **MLflow**; **api-gateway** starts after the other three app services have started. RabbitMQ can take up to ~90s on slower machines before its health check passes — a long pause with little output is normal.

### 3. Verify

```bash
make ps
```

You should see **eight** containers `Up`: `macro-postgres`, `macro-redis`, `macro-rabbitmq`, `macro-mlflow`, `macro-data-service`, `macro-ai-service`, `macro-alert-service`, and `macro-api-gateway`. Services with a health check may show `(healthy)` once ready.

| Check | URL or command |
|-------|----------------|
| All containers | `make ps` |
| BTC price (data-service) | `make price` |
| Per-service health | `make api-health`, `make ai-health`, `make alert-health`, or `make health` (data-service) |

**`null` for the first few seconds from `make price` is expected** — the Binance WebSocket has not delivered a tick yet.

Interactive API docs (Swagger): gateway **8000**, data **8001**, AI **8002**, alert **8003** — see [Health and API docs](#health-and-api-docs). For issues, `make logs` or service-specific targets such as `make data-logs`.

## Health and API docs

| Service | OpenAPI (`/docs`) | Health |
|---------|-------------------|--------|
| API Gateway | http://localhost:8000/docs | http://localhost:8000/health |
| Data service | http://localhost:8001/docs | http://localhost:8001/health |
| AI service | http://localhost:8002/docs | http://localhost:8002/health |
| Alert service | http://localhost:8003/docs | http://localhost:8003/health |

## Connecting the frontend

The browser talks only to the API gateway. From the repository root:

```bash
echo "VITE_API_GATEWAY_BASE_URL=http://localhost:8000" > frontend/.env.local
```

Then **restart the Vite dev server** — the variable is read at module load, so hot reload will not pick it up. Delete the file and restart to go back to simulated data.

A **"Simulated" badge** next to `BTC / USD` on the dashboard tells you which mode you are in, so you never have to infer it from config.

`localhost:8000` is right regardless of where the frontend is served from: the browser makes the request from your host, and Compose publishes the port. Container hostnames like `data-service:8001` only apply to server-to-server calls inside the Compose network.

## What is real once the backend is up

Starting the backend does not make every dashboard feature live. Current state:

| Frontend feature | Source | Why |
|---|---|---|
| Price, 24h/7d change, 24h high/low/volume | **Real** (when UI points at gateway) | Gateway proxies `GET /api/v1/btc/price`; data-service serves live Binance data |
| Price chart history | Simulated | `/price/history` is a placeholder ([#507](https://github.com/TheQuintet/macrocrypto-ai/issues/507)). The OHLCV data exists internally via `BinanceCollector.get_klines()`, just not over HTTP |
| Live price stream | Polling | No client-facing WebSocket exists ([#36](https://github.com/TheQuintet/macrocrypto-ai/issues/36)). data-service's socket is inbound only; the design docs assign a client stream to the API Gateway. The connection indicator reads "Polling" |
| Macro indicators | Empty | `FRED_API_KEY` is a placeholder. Free key: <https://fred.stlouisfed.org/docs/api/api_key.html>. BTC price needs no key |
| Forecasts / ML | Varies | ai-service and MLflow run in Compose; which routes the gateway exposes to the UI depends on current implementation — see [ai-service/README.md](./ai-service/README.md) |

## Services

Compose project name in Docker Desktop is typically **`macrocrypto-ai`** (folder name). Host ports below are the defaults from `docker-compose.yml`.

| Compose service | Container | Host port(s) | Purpose |
|-----------------|-----------|--------------|---------|
| `postgres` | `macro-postgres` | 5432 | TimescaleDB on Postgres 15 — primary datastore (`macrocrypto`, user `macro`) |
| `redis` | `macro-redis` | 6379 | Response and snapshot caching |
| `rabbitmq` | `macro-rabbitmq` | 5672 (AMQP), 15672 (mgmt UI) | Event bus; UI `guest` / `guest`. Override host ports with `RABBITMQ_AMQP_HOST_PORT` / `RABBITMQ_MGMT_HOST_PORT` if another stack uses the defaults |
| `mlflow` | `macro-mlflow` | 5000 | Model registry and experiment UI; ai-service uses `MLFLOW_TRACKING_URI=http://mlflow:5000` inside the network |
| `api-gateway` | `macro-api-gateway` | 8000 | External REST entry; proxies to internal services |
| `data-service` | `macro-data-service` | 8001 | BTC (Binance) and macro (FRED) collection; price and indicator APIs |
| `ai-service` | `macro-ai-service` | 8002 | BTC forecasting (Prophet, XGBoost, LightGBM) |
| `alert-service` | `macro-alert-service` | 8003 | Alert rules and notifications |

The **frontend** service block in `docker-compose.yml` is commented out, and there is no `frontend/Dockerfile`, so the dashboard does not run in Compose. Run it on the host — see [frontend/README.md](../frontend/README.md).

Per-service design and endpoints: [ai-service/README.md](./ai-service/README.md), [alert-service/README.md](./alert-service/README.md), [api-gateway/README.md](./api-gateway/README.md). data-service code lives under `services/data-service/`.

## data-service endpoints

Direct access on port **8001** (gateway may expose the same paths under **8000**):

| Endpoint | Purpose | Status |
|---|---|---|
| `GET /api/v1/btc/price` | Current snapshot: price, 24h change, 24h high/low/volume, 7d change. Redis-cached 5s | Live |
| `GET /api/v1/btc/price/history` | Historical prices | Placeholder — returns `[]` |
| `GET /api/v1/btc/status` | BTC pipeline status: price, cache and WebSocket state | Live |
| `GET /api/v1/indicators` | Latest macroeconomic indicators | Needs a FRED key |
| `GET /health` | Service health plus per-dependency status | Live |
| `GET /version` | Service and Python version | Live |
| `GET /docs` | Interactive OpenAPI docs | Live |

Rate limited to `RATE_LIMIT_REQUESTS`/minute (default 100). The `jwt_auth` dependency exists but is a passthrough — it validates nothing yet.

## Make commands

Run from the repository root; `make help` lists everything.

| Command | What it does |
|---|---|
| `make up` / `make down` | Start / stop all services |
| `make down-clean` | Stop **and drop volumes** — wipes the database and MLflow/RabbitMQ/Redis data |
| `make restart` | Restart all services |
| `make ps` | Container status |
| `make logs` | Tail logs for all services |
| `make build` | Rebuild images and start |
| `make clean` | Remove Python caches |

### data-service

| Command | What it does |
|---|---|
| `make data-up` / `make data-down` | Start (rebuilding if needed) / stop just data-service |
| `make data-restart` | Restart data-service |
| `make data-logs` | Tail data-service logs |
| `make data-shell` | Shell inside the container |
| `make data-test` | Full test suite |
| `make data-test-unit` / `make data-test-int` | Unit / integration tests only |
| `make data-test-cov` | Tests with coverage |
| `make data-lint` / `make data-format` | Lint / format |

### ai-service

| Command | What it does |
|---|---|
| `make ai-up` / `make ai-down` | Start (rebuild if needed) / stop ai-service |
| `make ai-restart` / `make ai-logs` / `make ai-shell` | Restart, logs, shell |
| `make ai-health` / `make ai-ready` | HTTP health / readiness |
| `make ai-test` / `make ai-test-cov` | Tests / coverage |
| `make ai-lint` / `make ai-format` | Lint / format |
| `make ai-run` | Run locally (outside Docker) |

### alert-service

| Command | What it does |
|---|---|
| `make alert-up` / `make alert-down` | Start (rebuild if needed) / stop alert-service |
| `make alert-restart` / `make alert-logs` / `make alert-shell` | Restart, logs, shell |
| `make alert-health` / `make alert-ready` | HTTP health / readiness |
| `make alert-test` / `make alert-test-cov` | Tests / coverage |
| `make alert-lint` / `make alert-format` | Lint / format |

### api-gateway

| Command | What it does |
|---|---|
| `make api-up` / `make api-down` | Start (rebuild if needed) / stop api-gateway |
| `make api-restart` / `make api-logs` / `make api-shell` | Restart, logs, shell |
| `make api-health` / `make api-ready` | HTTP health / readiness |
| `make api-test` / `make api-test-cov` | Tests / coverage |
| `make api-lint` / `make api-format` | Lint / format |
| `make api-run` | Run locally (outside Docker) |

### Infrastructure and monitoring

| Command | What it does |
|---|---|
| `make postgres-cli` | `psql` inside the Postgres container |
| `make redis-cli` | `redis-cli` inside the Redis container |
| `make rabbitmq-ui` | Open the RabbitMQ management UI (default http://localhost:15672) |
| `make mlflow-ui` | Open the MLflow UI (http://localhost:5000) |
| `make health` | Pretty-print data-service `/health` |
| `make price` | Pretty-print the current BTC price (data-service) |
| `make watch-price` | Live-refreshing price view (Ctrl+C to stop) |

## Running data-service without Docker

For debugging the service itself. Postgres, Redis and RabbitMQ still need to be reachable — point `DATABASE_URL`, `REDIS_HOST` and `RABBITMQ_HOST` at `localhost` in the env file, and use `make up` if you want Docker to provide them.

```bash
make setup
```

Creates a virtualenv at `services/data-service/venv` and installs `requirements.txt`.

```bash
make run
```

Uvicorn with `--reload` on port 8001.

Startup tolerates missing dependencies: database, Redis and RabbitMQ failures are caught and logged as warnings rather than aborting, so the service can come up **degraded rather than refusing to start**. Check `/health` rather than assuming a clean boot.

## Troubleshooting

Beyond the notes in [Quick start](#quick-start):

| Symptom | Cause |
|---|---|
| Stack stuck starting | Often RabbitMQ or MLflow health checks. `make ps` and `make logs` show which service is not healthy yet |
| data-service never turns healthy | Still waiting on postgres, redis, or rabbitmq. `make data-logs` for detail |
| `make price` prints the "not running" message | data-service is down, or `jq` is missing — try `curl http://localhost:8001/api/v1/btc/price` |
| Containers come back after you quit Docker | Services use `restart: unless-stopped`; use `make down` to stop the stack |
| Frontend still shows "Simulated" | Missing `VITE_API_GATEWAY_BASE_URL` in `frontend/.env.local`, or the dev server was not restarted |
| Real price, but chart and stream look fake | Expected — see [What is real once the backend is up](#what-is-real-once-the-backend-is-up) |
| RabbitMQ UI on a different host port | Another project may own 15672; check `RABBITMQ_MGMT_HOST_PORT` in your environment |

## Related documentation

- [frontend/README.md](../frontend/README.md) — frontend setup, scripts and testing
- [docs/README.md](../docs/README.md) — documentation home
- [docs/design/microservices.md](../docs/design/microservices.md) — service responsibilities and boundaries
- [docs/design/c4-model.md](../docs/design/c4-model.md) — system context and containers
- [GITHUB_FLOW.md](../GITHUB_FLOW.md) — branching and PR conventions
