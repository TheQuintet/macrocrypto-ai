# System E2E (Playwright)

Browser tests that expect a **running API gateway** (and backing services), not simulated frontend data.

## Run locally

1. Start the stack (gateway on port **8000**), e.g. `docker compose up` for postgres, redis, data-service, alert-service, api-gateway.
2. Point the Vite dev server at the gateway and run the **e2e** Playwright project:

```bash
cd frontend
VITE_API_GATEWAY_BASE_URL=http://127.0.0.1:8000 npm run test:e2e:system
```

If the gateway is down, specs **skip** with a short message (they do not fail).

## CI

The **System stack (Compose + live dashboard)** job sets `VITE_API_GATEWAY_BASE_URL` and runs these specs after the stack is healthy.

## vs UI integration

| Project | Folder | Backend |
|---------|--------|---------|
| `ui-integration` | `e2e/ui-integration/` | Optional (simulated data OK) |
| `e2e` | `e2e/system/` | Gateway required |
