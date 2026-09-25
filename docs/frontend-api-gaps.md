# Frontend API gaps

## Merged notifications (bell)

Price and prediction live in `in_app_notifications` (no list API on the gateway). Macro is `GET /api/v1/macro/notifications`.

| Method | Path |
|--------|------|
| `GET` | `/api/v1/notifications` — merge both sources, newest first, not archived |
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
