# Frontend API integration

Catalog of HTTP and WebSocket routes the **Vite frontend** calls when `VITE_API_GATEWAY_BASE_URL` is set. Paths are defined in `frontend/src/constants/apiUrls.ts`; fetchers live under `frontend/src/api/`.

For **missing backend work** (merged inbox, forecast proxy, price WebSocket), see [Frontend API gaps](./frontend-api-gaps.md).

## How integration works

| Mode | When | Behaviour |
|------|------|-----------|
| **Standalone** | `VITE_API_GATEWAY_BASE_URL` unset | Most screens use **simulated** data (`source: 'simulated'`). No gateway HTTP. |
| **Full-stack** | Gateway URL set | Fetchers call `{gateway}{path}`. Failures **throw** (error UI) except the **notification bell**, which can fall back to simulated data if live requests fail. |

Server data is loaded with **TanStack Query** (`frontend/src/hooks/use*Query.ts`, `use*Mutation.ts`). Local UI state uses **Zustand**, not the API layer.

**Source of truth for “Used” paths:** comments on each constant in `apiUrls.ts`.

---

## Summary

| Status | Count (approx.) | Meaning |
|--------|-----------------|--------|
| **Integrated** | 24 route patterns | UI wired; gateway proxies to data or alert service (or ai-service path documented as exception). |
| **Partial** | 5 | UI wired; some methods live, some simulated, or gateway/route missing for part of the feature. |
| **Wired, gateway gap** | 2 | UI calls the path; gateway does not expose it yet (forecast, price WebSocket). |
| **Not wired** | 17 | Listed in `unusedApiPaths` in `apiUrls.ts` — no frontend fetcher yet. |

---

## Integrated (working with gateway)

These routes are called from the app and forwarded by `services/api-gateway/app/api/v1/service_proxy.py` (data or alert service).

### Dashboard — Bitcoin

| Method | Path | Frontend module | UI |
|--------|------|-----------------|-----|
| `GET` | `/api/v1/btc/price` | `api/btcPrice/btcPrice.ts` | Live price card; **polls** when the stream is disconnected |
| `GET` | `/api/v1/btc/price/history` | `api/btcPrice/btcPriceHistory.ts` | Dashboard chart time ranges |

### Dashboard — macro indicators

| Method | Path | Frontend module | UI |
|--------|------|-----------------|-----|
| `GET` | `/api/v1/indicators` | `api/macroIndicators/macroIndicators.ts` | Latest CPI / Fed funds / GDP (main names) |
| `GET` | `/api/v1/indicators?period=…` | `api/macroIndicators/macroIndicatorHistory.ts` | Indicator history chart (`30d` / `90d` / `1y` / `5y`) |

### Macro Economy — calendar

| Method | Path | Frontend module | UI |
|--------|------|-----------------|-----|
| `GET` | `/api/v1/economic-calendar` | `api/economicCalendar/economicCalendar.ts` | Economic calendar grid |

### Macro Economy — regime analysis

| Method | Path | Frontend module | UI |
|--------|------|-----------------|-----|
| `GET` | `/api/v1/regimes/current` | `api/regimes/currentRegime.ts` | Current regime card |
| `GET` | `/api/v1/regimes` | `api/regimes/regimeHistory.ts` | Regime timeline |
| `GET` | `/api/v1/regimes/performance` | `api/regimes/regimePerformance.ts` | Performance by regime |
| `GET` | `/api/v1/regimes/history/similar-periods?limit=3–5` | `api/regimes/similarPeriods.ts` | Similar historical periods |

### Forecasts — chart history only

| Method | Path | Frontend module | UI |
|--------|------|-----------------|-----|
| `GET` | `/api/v1/btc/price/history?range=…&interval=…` | `api/predictions/predictionHistory.ts` | Actual candles behind the forecast chart |

### Alerts — price

| Method | Path | Frontend module | UI |
|--------|------|-----------------|-----|
| `GET` | `/api/v1/alerts/price` | `api/alerts/priceAlerts.ts` | List (query: `user_id`, pagination) |
| `POST` | `/api/v1/alerts/price` | same | Create |
| `GET` | `/api/v1/alerts/price/{alert_id}` | same | Read one |
| `PUT` | `/api/v1/alerts/price/{alert_id}` | same | Update |
| `DELETE` | `/api/v1/alerts/price/{alert_id}` | same | Delete |
| `POST` | `/api/v1/alerts/price/{alert_id}/trigger` | same | Manual trigger |

### Alerts — prediction

| Method | Path | Frontend module | UI |
|--------|------|-----------------|-----|
| `GET` | `/api/v1/alerts/prediction/` | `api/alerts/predictionAlerts.ts` | List (`user_id`) |
| `POST` | `/api/v1/alerts/prediction/` | same | Create |
| `GET` | `/api/v1/alerts/prediction/{alert_id}` | same | Read / toggle status |
| `PUT` | `/api/v1/alerts/prediction/{alert_id}` | same | Update |
| `DELETE` | `/api/v1/alerts/prediction/{alert_id}` | same | Delete |

### Alerts — macro subscriptions

| Method | Path | Frontend module | UI |
|--------|------|-----------------|-----|
| `GET` | `/api/v1/macro/subscriptions/{user_id}` | `api/alerts/macroAlerts.ts`, `macroSubscriptions.ts` | Subscription list |
| `POST` | `/api/v1/macro/subscribe` | `api/alerts/macroAlerts.ts` | Subscribe / update one event type |

### Alerts — macro notification history (dedicated page)

| Method | Path | Frontend module | UI |
|--------|------|-----------------|-----|
| `GET` | `/api/v1/macro/notifications/{user_id}` | `api/alerts/macroAlertHistory.ts` | Macro alert history table |

### In-app bell (notifications)

| Method | Path | Frontend module | UI |
|--------|------|-----------------|-----|
| `GET` | `/api/v1/macro/notifications` | `api/alerts/notifications.ts` | Inbox list (shared demo; `limit` / `offset`) |
| `PUT` | `/api/v1/macro/notifications/{notification_id}/read` | same | Mark one read |
| `POST` | `/api/v1/macro/notifications/read-all` | same | Mark all read |

Unread count is derived from the list (`read: false`), not a separate client call to `GET …/unread` (that route exists on the gateway but the inbox does not use it).

With gateway configured, the bell **polls** on an interval; there is no live notification stream (see partial gaps below).

---

## Partial integration

Features where the UI is wired but not every path is live end-to-end.

| Area | What works | What does not |
|------|------------|----------------|
| **Forecasts** | `GET /api/v1/btc/price/history` | `GET /api/v1/predict/btc` — implemented on **ai-service**, **not** proxied on gateway → forecast line errors when gateway is set |
| **Dashboard price stream** | `GET /api/v1/btc/price` polling | `WS /api/v1/btc/price/stream` — UI opens a WebSocket when gateway is set, but gateway route is not enabled → status **Disconnected**, polling continues |
| **Inbox** | Macro notifications REST | **Macro-only** until `GET /api/v1/notifications` merges price + prediction + macro; no WebSocket/SSE stream when gateway is set |
| **Price alert history** | Simulated when no gateway | `GET /api/v1/alerts/price/{alert_id}/history` — called from UI, **not** in gateway proxy list |
| **Prediction alert history / export** | CRUD live | History and CSV export return **empty / stub** when gateway is set (no dedicated routes wired in UI) |

---

## Wired in frontend, not on gateway

| Method | Path | Frontend module | Notes |
|--------|------|-----------------|-------|
| `GET` | `/api/v1/predict/btc?horizon=&confidence=` | `api/predictions/btcPrediction.ts` | Needs ai-service proxy on gateway |
| `WS` | `/api/v1/btc/price/stream` | `lib/priceSocket.ts`, `hooks/usePriceStream.ts` | See [gaps doc](./frontend-api-gaps.md) |

---

## Not wired in the frontend yet

Constants are reserved in `unusedApiPaths` (`apiUrls.ts`). No production fetcher uses these today.

**Data service:** `/api/v1/btc/dominance`, `/api/v1/btc/status`, `/api/v1/regimes/btc`, `/api/v1/regimes/{regime_id}`

**Alert service:** prediction config, macro unsubscribe-all helpers, macro alert rules CRUD, macro upcoming events

**AI service:** `/api/v1/performance/btc`, `/api/v1/correlation/btc`, exports, methodology, historical events

---

## Quick map: screen → APIs

| Screen / feature | Primary APIs |
|------------------|--------------|
| Dashboard (BTC) | `btc/price`, `btc/price/history`, `WS btc/price/stream` (stream gap) |
| Dashboard (indicators) | `indicators`, `indicators?period=` |
| Forecasts | `predict/btc` (gap), `btc/price/history` |
| Regime analysis | four `regimes/*` routes above |
| Economic calendar | `economic-calendar` |
| Alerts management | `alerts/price`, `alerts/prediction/`, `macro/subscriptions`, `macro/subscribe` |
| Macro alert history page | `macro/notifications/{user_id}` |
| Notification bell | `macro/notifications`, read / read-all |

---

## Maintenance

When you wire a new screen to the gateway:

1. Add or mark the path **Used** in `frontend/src/constants/apiUrls.ts`.
2. Implement the fetcher under `frontend/src/api/`.
3. Remove the path from `unusedApiPaths` if it was listed there.
4. Update this doc and [frontend-api-gaps.md](./frontend-api-gaps.md) if gateway coverage changes.
