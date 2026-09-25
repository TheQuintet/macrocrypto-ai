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

## Other missing routes

| UI | Path |
|----|------|
| Price stream | `WS /api/v1/btc/price/stream` |
| Forecast | `GET /api/v1/predict/btc` |

Price snapshot still works via `GET /api/v1/btc/price`.
