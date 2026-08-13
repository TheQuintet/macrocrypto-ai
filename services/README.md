# MacroCrypto AI — Services (Backend)

Backend microservices and the infrastructure they depend on, run through Docker Compose from the repository root.

Only **data-service** is active today; the other folders are scaffolding. See [Services](#services).

## Prerequisites

- **Docker Desktop**, installed *and running*. `docker info` errors if it is installed but not started.
- `make` (preinstalled on macOS and Linux).
- `jq`, optional — only `make health`, `make price` and `make watch-price` use it.

## Quick start

### 1. Create the data-service env file

```bash
cp services/data-service/.env.example services/data-service/.env
```

**Required.** `docker-compose.yml` declares `env_file: ./services/data-service/.env`, so Compose fails immediately without it. The file is gitignored, so it is never in a fresh clone — this is the step that usually blocks people.

No edits needed. The defaults use Compose service names (`postgres`, `redis`, `rabbitmq`) rather than `localhost`, which is what the containers need.

### 2. Start

```bash
make up
```

The first run takes a few minutes — it builds the data-service image and pulls three base images. Later starts take seconds.

data-service declares `depends_on: condition: service_healthy`, so it waits for Postgres, Redis and RabbitMQ to pass their health checks before starting. A pause with no output is normal.

### 3. Verify

```bash
make ps
```

Four containers `Up`, with data-service `(healthy)`.

```bash
make price
```

Returns the current BTC snapshot. **`null` for the first few seconds is expected** — the Binance WebSocket has not delivered a tick yet.

For anything unexpected, `make health` breaks down each dependency and `make data-logs` shows the service log. Interactive API docs: <http://localhost:8001/docs>

## Connecting the frontend

The browser calls data-service directly on `localhost`, so from the repository root:

```bash
echo "VITE_API_BASE_URL=http://localhost:8001" > frontend/.env.local
```

Then **restart the Vite dev server** — the variable is read at module load, so hot reload will not pick it up. Delete the file and restart to go back to simulated data.

A **"Simulated" badge** next to `BTC / USD` on the dashboard tells you which mode you are in, so you never have to infer it from config.

`localhost:8001` is right regardless of where the frontend is served from: the browser makes the request from your host, and Compose publishes the port. Container hostnames like `data-service:8001` only apply to server-to-server calls inside the Compose network.

## What is real once the backend is up

Starting the backend does not make everything live. Current state:

| Frontend feature | Source | Why |
|---|---|---|
| Price, 24h/7d change, 24h high/low/volume | **Real** | `GET /api/v1/btc/price` serves live Binance data |
| Price chart history | Simulated | `/price/history` is a placeholder ([#507](https://github.com/TheQuintet/macrocrypto-ai/issues/507)). The OHLCV data exists internally via `BinanceCollector.get_klines()`, just not over HTTP |
| Live price stream | Polling | No client-facing WebSocket exists ([#36](https://github.com/TheQuintet/macrocrypto-ai/issues/36)). data-service's socket is inbound only; the design docs assign a client stream to the API Gateway, still a scaffold. The connection indicator reads "Polling" |
| Macro indicators | Empty | `FRED_API_KEY` is a placeholder. Free key: <https://fred.stlouisfed.org/docs/api/api_key.html>. BTC price needs no key |

## Services

| Service | Container | Port | Purpose | Status |
|---|---|---|---|---|
| `data-service` | `macro-data-service` | 8001 | Collects BTC data from Binance and macro data from FRED; serves the price and indicator APIs | **Active** |
| postgres | `macro-postgres` | 5432 | Primary datastore (`macrocrypto` db, user `macro`) | **Active** |
| redis | `macro-redis` | 6379 | Response and snapshot caching | **Active** |
| rabbitmq | `macro-rabbitmq` | 5672, 15672 | Event bus; management UI on 15672 (`guest`/`guest`) | **Active** |
| `ai-service` | — | 8002 | Prophet price forecasting | Commented out in Compose |
| `alert-service` | — | — | Alert rules and notifications | Commented out in Compose |
| `api-gateway` | — | — | REST + WebSocket gateway | Commented out; folder is empty `__init__.py` stubs |

The frontend is in `docker-compose.yml` too but commented out, and there is no `frontend/Dockerfile`, so it cannot start that way. Run it on the host — see [frontend/README.md](../frontend/README.md).

## data-service endpoints

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
| `make down-clean` | Stop **and drop volumes** — wipes the database |
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

### Infrastructure and monitoring

| Command | What it does |
|---|---|
| `make postgres-cli` | `psql` inside the Postgres container |
| `make redis-cli` | `redis-cli` inside the Redis container |
| `make rabbitmq-ui` | Open the RabbitMQ management UI |
| `make health` | Pretty-print `/health` |
| `make price` | Pretty-print the current BTC price |
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
| data-service never turns healthy | Still waiting on a dependency's health check. `make ps` shows which, `make logs` shows why |
| `make price` prints the "not running" message | Service is down, or `jq` is missing — compare against `curl http://localhost:8001/api/v1/btc/price` |
| Containers come back after you quit Docker | data-service uses `restart: unless-stopped`; use `make down` to stop it properly |
| Frontend still shows "Simulated" | Missing variable in `frontend/.env.local`, or the dev server was not restarted |
| Real price, but chart and stream look fake | Expected — see [What is real once the backend is up](#what-is-real-once-the-backend-is-up) |

## Related documentation

- [frontend/README.md](../frontend/README.md) — frontend setup, scripts and testing
- [docs/README.md](../docs/README.md) — documentation home
- [docs/design/microservices.md](../docs/design/microservices.md) — service responsibilities and boundaries
- [docs/design/c4-model.md](../docs/design/c4-model.md) — system context and containers
- [GITHUB_FLOW.md](../GITHUB_FLOW.md) — branching and PR conventions
