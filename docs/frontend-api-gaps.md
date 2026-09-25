# Frontend API gaps

## Merged notifications (bell)

The bell needs **one list** with all alert types:

| Type | `notification_type` | Where it lives today |
|------|---------------------|----------------------|
| Price alerts | `price_alert` | `in_app_notifications` (no list API on gateway) |
| Prediction alerts | `prediction_alert` | `in_app_notifications` (same) |
| Macro alerts | `macro_alert` | `macro_event_notifications` — `GET /api/v1/macro/notifications` only |

`GET /api/v1/notifications` must **merge price + prediction + macro** into a single response (newest first, not archived). Macro-only is not enough for the inbox.

| Method | Path |
|--------|------|
| `GET` | `/api/v1/notifications` — merged price, prediction, and macro |
| `PUT` | `/api/v1/notifications/{id}/read` |
| `POST` | `/api/v1/notifications/read-all` → `{ "count": number }` |

Shared demo inbox: no `user_id` filter.

**`GET /api/v1/notifications` body:**

```json
{
  "total": 0,
  "limit": 50,
  "offset": 0,
  "notifications": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "alert_id": "uuid-or-null",
      "title": "string",
      "message": "string",
      "notification_type": "price_alert | prediction_alert | confidence_alert | macro_alert",
      "data": {},
      "action_url": "string-or-null",
      "read": false,
      "is_archived": false,
      "created_at": "ISO-8601",
      "read_at": "ISO-8601-or-null"
    }
  ]
}
```

Macro: `event_name` → `title`, `description` → `message`, `sent_at` → `created_at`, `notification_type`: `macro_alert`.

## Forecasts screen

The Forecasts page (`PredictionPanel`) uses **two** data routes:

| Part | Method | Path | Status |
|------|--------|------|--------|
| Chart history (actual candles) | `GET` | `/api/v1/btc/price/history` | **On gateway** (data service proxy) |
| Forecast batch (line + band + summary) | `GET` | `/api/v1/predict/btc` | **Missing on gateway** — implemented on **ai-service**, not proxied in `service_proxy.py` |

With `VITE_API_GATEWAY_BASE_URL` set, history loads live but the forecast call **404s** until the gateway forwards ai-service predict routes.

### Missing: proxy `GET /api/v1/predict/btc`

| Method | Path |
|--------|------|
| `GET` | `/api/v1/predict/btc` |

**Query params** (what the UI sends today):

| Param | Values | Notes |
|-------|--------|--------|
| `horizon` | `24h`, `7d` | Required for the screen |
| `confidence` | `0.7`, `0.85`, `0.95` | Confidence band width |
| `model_name` | e.g. `prophet` | Optional; UI omits this (single-model default) |
| `models` | comma-separated | Optional; **not used** by Forecasts (multi-model returns a different envelope) |

**Response** must match `frontend/src/types/predictions.ts` / ai-service `PredictionResponse`:

```json
{
  "horizon": "24h",
  "model_name": "prophet",
  "confidence": 0.85,
  "prediction_time": "ISO-8601",
  "current_price": 95000.0,
  "predicted_end_price": 96500.0,
  "price_change_pct": 1.58,
  "trend": "up | down | neutral",
  "predictions": [
    {
      "time": "ISO-8601",
      "predicted_price": 95200.0,
      "lower_bound": 94000.0,
      "upper_bound": 96400.0
    }
  ]
}
```

**History query** (already works — for reference):

`GET /api/v1/btc/price/history?range=24h|7d|30d&interval=1h|1d` — the UI picks `range` / `interval` from the selected forecast horizon (wider lookback than the forecast window).

### Not required for the current Forecasts UI

| Path | Notes |
|------|--------|
| `GET /api/v1/performance/btc` | Model accuracy on ai-service; no Forecasts screen yet |
| `GET /api/v1/btc/price` | Snapshot; forecast summary uses `current_price` on the predict response |

Prediction **alerts** (`/api/v1/alerts/prediction/…`) are already on the gateway; they are separate from the Forecasts chart.

## Regime analysis

Regime routes are **implemented** (data service + gateway proxy). The UI calls:

- `GET /api/v1/regimes/current`
- `GET /api/v1/regimes`
- `GET /api/v1/regimes/performance`
- `GET /api/v1/regimes/history/similar-periods`

Optional combined route `GET /api/v1/regimes/btc` exists but the frontend uses the split routes above.

## Other missing routes

| UI | Path |
|----|------|
| Dashboard price stream | `WS /api/v1/btc/price/stream` |

Price snapshot still works via `GET /api/v1/btc/price`. REST polling works when the WebSocket route is absent.
