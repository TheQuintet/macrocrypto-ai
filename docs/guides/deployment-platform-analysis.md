# MacroCrypto AI — Deployment Platform Analysis

_Last updated: 2026-10-11_

## Summary

Deploy the whole stack to **one Linux VM (4 vCPU, 8–16 GB RAM, 50+ GB SSD) running Docker Compose**. No GPU is needed.

The models are CPU-bound tabular and time-series models: Prophet, XGBoost, LightGBM and scikit-learn. They retrain once a day inside `ai-service`. A single VM gives that job enough CPU and RAM, and it gives persistent disk for model files, MLflow artifacts and TimescaleDB. It also reuses the existing `docker-compose.yml`, so the deploy needs the least new work before the demo.

Recommended providers, in order: Hetzner Cloud (cheapest), DigitalOcean (covered by GitHub Student Pack credit), or AWS EC2 / GCP Compute Engine if the team already has credits there.

## What we are deploying

The app is 9 containers, all defined in `docker-compose.yml`. The frontend is a static Vite build.

| Component | Image / source | Role | Needs persistent data |
| --- | --- | --- | --- |
| postgres | `timescale/timescaledb:2.17.2-pg15` | Main database, time-series storage | Yes |
| redis | `redis:7-alpine` | Cache (predictions, prices) | Optional |
| rabbitmq | `rabbitmq:3-management-alpine` | Event bus between services | Yes |
| mlflow | `ghcr.io/mlflow/mlflow:v2.18.0` | Experiment tracking, model registry | Yes |
| data-service | `services/data-service` | Ingests market and macro data | No |
| ai-service | `services/ai-service` | Predictions and daily retraining | Yes (model files) |
| alert-service | `services/alert-service` | Price alerts and notifications | No |
| api-gateway | `services/api-gateway` | Single public API for the frontend | No |
| frontend | `frontend/` (Vite + React) | Web UI, built to static files | No |

**ML workload.** `ai-service` uses Prophet, XGBoost, LightGBM, scikit-learn, pandas and MLflow (`services/ai-service/requirements.txt`). None of these need a GPU for this data size. An APScheduler job (`app/scheduler/jobs.py`) retrains all 6 model variants daily at 06:00 UTC. It saves each variant to local disk and logs runs to MLflow.

## Requirements from the codebase

The platform must run long-lived containers with persistent disk; GPU is not a requirement.

| Need | Why | Implication |
| --- | --- | --- |
| CPU for training | Daily retrain of 6 variants (Prophet, XGBoost, LightGBM) | 4 vCPU is enough; training takes minutes, not hours |
| RAM | 9 containers + pandas frames during training | 8 GB minimum, 16 GB comfortable |
| Persistent disk | Postgres/Timescale, RabbitMQ, MLflow artifacts, saved model files | Volumes that survive restarts and redeploys |
| Always-on processes | Scheduler, RabbitMQ consumers, alert checks | No scale-to-zero or cold starts |
| Private networking | Services call each other by name (`postgres`, `rabbitmq`, `mlflow`) | All services on one network; only the gateway and UI are public |
| Public HTTPS | Frontend and API gateway | Reverse proxy with TLS |

Open question: the expected data volume after a few months of ingestion. It decides whether 50 GB of disk lasts.

## Platform options compared

A single VM with Docker Compose fits best: it matches how the app already runs and handles training with no extra parts.

| Option | Examples | Fit for this app | Main drawback |
| --- | --- | --- | --- |
| **VM + Docker Compose** (recommended) | Hetzner Cloud, DigitalOcean Droplet, AWS EC2, GCP Compute Engine | Runs the existing compose file almost as is; persistent disk; full CPU for training | We patch the OS, run backups and set up TLS ourselves |
| PaaS | Render, Railway, Fly.io | Simple deploys per service | Billed per service (9 here); per-container memory caps; TimescaleDB and RabbitMQ are hard to host; weak persistent volumes |
| Managed ML | AWS SageMaker, GCP Vertex AI | Strong for large or GPU training | Overkill and costly for CPU models; still need a host for the other 8 services |
| Managed containers | AWS ECS/Fargate, GCP Cloud Run, Azure Container Apps | Scales well, managed runtime | Much more setup (networking, IAM, managed DB, queues); Cloud Run scale-to-zero breaks the scheduler |
| Kubernetes | EKS, GKE, DOKS | Production-grade scaling | Far too much operational work for a 9-container student project |

Prices vary by region and change often, so they are left out here; check each provider's pricing page before choosing.

## Recommendation and sizing

Choose the provider by where the team has credits; the setup is the same on all four.

| Provider | Suggested instance | vCPU / RAM | When to pick it |
| --- | --- | --- | --- |
| Hetzner Cloud | CX32 or CX42 | 4 / 8 GB or 8 / 16 GB | Lowest cost, EU data centres |
| DigitalOcean | Basic or General Purpose Droplet | 4 / 8 GB or 4 / 16 GB | GitHub Student Pack credit available |
| AWS EC2 | t3.xlarge or m6i.xlarge | 4 / 16 GB | Team or course already has AWS credits |
| GCP Compute Engine | e2-standard-4 | 4 / 16 GB | Team or course already has GCP credits |

Use Ubuntu 24.04 LTS, at least 50 GB SSD and a static public IP. Point a domain (or a free subdomain) at it for TLS.

![Target deployment: the frontend is served by Cloudflare, and the API and all services run on one VM with Docker Compose](../images/deployment-architecture.svg)

The browser loads the frontend from Cloudflare. API calls go only to nginx on 443 on the VM. Services reach the databases, queue and MLflow by name on the private Docker network, and stateful data lives on persistent volumes that are backed up nightly.

## Production readiness changes

The current compose file is set up for local development and needs a `docker-compose.prod.yml` override before going public.

- [x] Remove dev bind mounts (`./services/*/app:/app/app`, `./shared:/app/shared`) so images run the code they were built with
- [ ] Replace hardcoded credentials. Postgres is done via `POSTGRES_PASSWORD`. RabbitMQ `guest`/`guest` is still open: it must change in the broker and in the four services' `.env` files together
- [x] Stop publishing internal ports (5432, 6379, 5672, 15672, 5000, 8000–8003) to the host; expose only 80/443
- [x] Enable the reverse proxy (Caddy, which gets TLS certificates automatically) for `api.<domain>` only
- [ ] Deploy the frontend to Cloudflare (see [Frontend deploy on Cloudflare](#frontend-deploy-on-cloudflare)), not from the VM
- [x] Add a named volume for `ai-service` model files so trained models survive redeploys
- [ ] Move MLflow's backend store from SQLite to the Postgres instance (optional, more robust)
- [ ] Set the gateway's `CORS_ALLOW_ORIGINS` to the Cloudflare Worker URL
- [ ] Add a nightly `pg_dump` backup copied off the server

## Frontend deploy on Cloudflare

**Why Cloudflare:** we first chose Vercel, but its Hobby plan can't deploy from a private GitHub organisation repo. The Vercel prompt asked for a Pro plan. Cloudflare deploys this repo on its free plan. The repo contains `frontend/wrangler.jsonc`, which serves `dist` as a single-page app.

**Current status:** deploy without the API variable for now, so the site shows simulated data. Add the variable and the VM CORS setting later, once the API domain is ready.

**Steps: first deploy**

1. In the Cloudflare dashboard, click **Compute → Workers & Pages → Create → Create an app**.
2. Under **Select a method**, choose **Connect a Git repository**, not **Clone a public repository via Git URL**.
3. If `macrocrypto-ai` isn't listed, click **Configure GitHub**, grant Cloudflare access to the TheQuintet organisation, and select the repo.
4. Select `TheQuintet/macrocrypto-ai` and click **Next**.
5. Set **Build command** to `npm run build`.
6. Set **Deploy command** to `npx wrangler deploy`. Leave the default.
7. Turn off **Enable Preview builds**.
8. Open **Advanced settings** and set **Path** to `/frontend`.
9. Under **Advanced settings**, leave **API token** as **Create new token**, and leave **API token name** empty.
10. Click **Deploy**.
11. Open the Worker's **Domains** tab. Under **Worker URL**, copy the **Production** address, in the form `https://macrocrypto-ai.lgloredanaelena.workers.dev`.
12. Open the site. Simulated data appears, and reloading `/macro` loads the page.

**Steps: connect the API (later)**

Do these once the API domain `https://api.<your-domain>` serves HTTPS from the VM.

1. In the Worker's settings, add the variable `VITE_API_GATEWAY_BASE_URL` = `https://api.<your-domain>`. Leave **Encrypt** off.
2. Start a new deployment from the Worker's **Deployments** page. The variable applies only to a new build.
3. On the VM, set `CORS_ALLOW_ORIGINS=["https://macrocrypto-ai.lgloredanaelena.workers.dev"]` and restart `api-gateway`.
4. Open the site. In DevTools → Network, API calls go to `https://api.<your-domain>/...` with no CORS errors. Live data replaces the simulated data.

**If something fails**
- Repo not listed → repeat step 3.
- Build error "package.json not found" → **Path** must be `/frontend` (step 8).
- Deployment fails at the deploy step → check that `frontend/wrangler.jsonc` is in the repo.
- CORS error after connecting the API → repeat connect step 3.

## Deployment of the backend

Current deployment: Hetzner Cloud, Helsinki, Ubuntu 24.04, 8 GB RAM. The server IP is kept out of the repo; use `<server-ip>` below and see the server notes for the real value.
API: `https://api.<ip-with-dashes>.sslip.io` · Docs: `https://api.<ip-with-dashes>.sslip.io/docs`

### 1. SSH key and server (Hetzner)

SSH keys belong to a Cloud **project** (console.hetzner.com), not to account settings (accounts.hetzner.com).

1. On your laptop, create a dedicated key. `-f` keeps existing keys untouched:
   `ssh-keygen -t ed25519 -C "<name>-macrocrypto" -f ~/.ssh/macrocrypto_hetzner`
   Passphrase: recommended. It protects the key file and is not a Hetzner password.
2. Open the project → **Security → SSH keys → Add SSH key**, and paste the contents of `~/.ssh/macrocrypto_hetzner.pub`. Never paste the private key.
3. **Add Server**: Ubuntu 24.04, ≥4 vCPU / 8 GB, tick the SSH key(s).
4. Log in: `ssh -i ~/.ssh/macrocrypto_hetzner root@<server-ip>`

**Teammate access:** keys added in Hetzner *after* the server exists are not copied to it. Add them on the server instead:
`echo "<their .pub line>" >> /home/deploy/.ssh/authorized_keys`

### 2. Harden the server (as root, once)

```bash
apt update && apt upgrade -y && reboot
adduser deploy && usermod -aG sudo deploy
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

Check that `ssh -i ~/.ssh/macrocrypto_hetzner deploy@<server-ip>` works **before** continuing. Then, as `deploy`:

```bash
sudo ufw allow OpenSSH && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw --force enable
printf "PermitRootLogin no\nPasswordAuthentication no\n" | sudo tee /etc/ssh/sshd_config.d/00-hardening.conf && sudo systemctl restart ssh
sudo apt install -y unattended-upgrades && sudo dpkg-reconfigure -f noninteractive unattended-upgrades
```

From now on, log in only as `deploy`. Root SSH login is disabled.

### 3. Docker

```bash
curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker deploy
```

Log out and back in, then check: `docker compose version`.

### 4. Get the code

Deploy keys are **disabled by the TheQuintet org policy**, so use a fine-grained personal access token instead:
GitHub → Settings → Developer settings → Fine-grained tokens. Resource owner: **TheQuintet**. Repository: **macrocrypto-ai** only. Permission: **Contents: Read-only**.

```bash
read -s T            # paste the token, press Enter
printf "https://<github-user>:%s@github.com\n" "$T" > ~/.git-credentials && chmod 600 ~/.git-credentials && unset T
git config --global credential.helper store
git clone https://github.com/TheQuintet/macrocrypto-ai.git && cd macrocrypto-ai
```

### 5. Production override and secrets

`docker-compose.prod.yml` (in the repo):
- removes all published ports except Caddy's 80/443; the gateway binds only to `127.0.0.1:8000`
- replaces the hardcoded Postgres password with `${POSTGRES_PASSWORD}`
- adds **Caddy** as the HTTPS reverse proxy (automatic Let's Encrypt) for `${API_DOMAIN}`
- puts trained models on a named volume so they survive redeploys

The MLflow healthcheck is fixed in the base `docker-compose.yml`: the MLflow image has no `curl`, so the original check always failed.

> ⚠️ Never run plain `docker compose up` on the server. Docker-published ports bypass `ufw`, so the dev compose file would expose Postgres, Redis and RabbitMQ to the internet.

Create the root `.env` (see the root `.env.example` for the variables) and the service env files:

```bash
printf "POSTGRES_PASSWORD=%s\nAPI_DOMAIN=api.<ip-with-dashes>.sslip.io\n" "$(openssl rand -hex 16)" > .env && chmod 600 .env
for s in data-service alert-service ai-service api-gateway; do cp services/$s/.env.example services/$s/.env; done
```

`sslip.io` gives a free hostname that resolves to the IP, so no DNS setup is needed. Never commit `.env` files.

### 6. Start and verify

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

- All 9 containers are `Up`/`healthy`. Only `macro-caddy` shows `0.0.0.0:` ports.
- `https://api.<ip-with-dashes>.sslip.io/health` returns `"status":"healthy"` with database and RabbitMQ connected.
- `https://api.<ip-with-dashes>.sslip.io/docs` opens Swagger.

### 7. Connect the frontend (Cloudflare)

`VITE_*` values are compiled in at **build time**:

1. Worker → **Settings → Build → Variables and secrets** (not the runtime variables): `VITE_API_GATEWAY_BASE_URL=https://api.<ip-with-dashes>.sslip.io`
2. Trigger a new build (push to `main` or Retry build).
3. On the server, set `CORS_ALLOW_ORIGINS=["https://macrocrypto-ai.lgloredanaelena.workers.dev"]` in `services/api-gateway/.env`, then run:
   `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate api-gateway`

### Redeploy

```bash
cd ~/macrocrypto-ai && git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

After changing any `.env` file, add `--force-recreate` to the `up` command for the affected service, for example `up -d --force-recreate api-gateway`. A plain `up -d` may keep the old environment.

### Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Failed to connect to system scope bus` during `apt upgrade` | Harmless. Rerun `apt upgrade -y`, then `reboot`. |
| `ls` shows no repo | You're root (`root@…`). Run `su - deploy`; the repo is in `/home/deploy`. |
| `git clone`: invalid username or token | Token pasted wrongly or pending org approval. Use the `read -s` method in step 4. |
| `macro-mlflow is unhealthy` | `curl` missing in the MLflow image. The Python healthcheck in `docker-compose.yml` fixes it. |
| `deploy@…'s password:` when connecting | Key not copied to `deploy`. Rerun the `rsync` line as root. |

### Still to do

- RabbitMQ still uses `guest/guest`. It's internal only, but replace it with real credentials.
- Nightly `pg_dump` backup copied off the server.
- Optional: GitHub Actions deploy over SSH.

## Future scaling

Keep the app on the VM. Move only training elsewhere if one of these happens:

- **Deep learning models** (LSTMs, transformers): run training as a separate job on a GPU instance or a service such as Modal. Log to the same MLflow server, and let `ai-service` load the registered model.
- **Retraining slows the live API**: move the retrain job into its own container, or onto a second VM, so prediction serving keeps its CPU.
- **Data outgrows the disk or needs high availability**: move Postgres to a managed database (with TimescaleDB support) and MLflow artifacts to object storage (S3, GCS, Spaces).
