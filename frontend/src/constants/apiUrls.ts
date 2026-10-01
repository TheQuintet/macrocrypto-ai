import { apiUrl, wsUrl } from '@/lib/apiConfig'

// ---------------------------------------------------------------------------
// Data service
// ---------------------------------------------------------------------------

/** Used. GET current BTC snapshot. */
export const BTC_PRICE_PATH = '/api/v1/btc/price'
/** Used. GET candle history. */
export const BTC_PRICE_HISTORY_PATH = '/api/v1/btc/price/history'
/** Used. GET latest CPI / Fed funds / GDP prints. */
export const MACRO_INDICATORS_PATH = '/api/v1/indicators'
/** Used. GET calendar events. */
export const ECONOMIC_CALENDAR_PATH = '/api/v1/economic-calendar'
/** Used. GET the active regime card. */
export const CURRENT_REGIME_PATH = '/api/v1/regimes/current'
/** Used. GET regime history / timeline. */
export const REGIME_HISTORY_PATH = '/api/v1/regimes'
/** Used. GET performance-by-regime rows. */
export const REGIME_PERFORMANCE_PATH = '/api/v1/regimes/performance'
/** Used. GET similar historical periods. */
export const SIMILAR_PERIODS_PATH = '/api/v1/regimes/history/similar-periods'

/** Unused. GET BTC dominance. */
export const BTC_DOMINANCE_PATH = '/api/v1/btc/dominance'
/** Unused. GET BTC feed / collector status. */
export const BTC_STATUS_PATH = '/api/v1/btc/status'
/**
 * Unused. Combined current + history + similar periods + event analysis.
 * The frontend calls those as separate routes so each regime tab can load
 * and fail on its own.
 */
export const REGIME_BTC_PATH = '/api/v1/regimes/btc'
/** Unused. GET one regime by id. */
export const REGIME_BY_ID_PATH = '/api/v1/regimes/{regime_id}'

// ---------------------------------------------------------------------------
// Alert service
// ---------------------------------------------------------------------------

/** Used. GET/POST price-alert collection. */
export const PRICE_ALERTS_PATH = '/api/v1/alerts/price'
/** Used. GET/PUT/DELETE one price alert. */
export const PRICE_ALERT_PATH = `${PRICE_ALERTS_PATH}/{alert_id}`
/** Used. POST a manual trigger. */
export const PRICE_ALERT_TRIGGER_PATH = `${PRICE_ALERTS_PATH}/{alert_id}/trigger`
/** Used. GET/POST prediction-alert collection. */
export const PREDICTION_ALERTS_PATH = '/api/v1/alerts/prediction/'
/** Used. GET/PUT/DELETE one prediction alert. */
export const PREDICTION_ALERT_PATH = `${PREDICTION_ALERTS_PATH}{alert_id}`
/** Used. GET a user's event subscriptions. */
export const MACRO_SUBSCRIPTIONS_PATH = '/api/v1/macro/subscriptions'
/** Used. POST subscribe / update one event type. */
export const MACRO_SUBSCRIBE_PATH = '/api/v1/macro/subscribe'
/** Used. GET sent macro notifications for a user. */
export const MACRO_ALERT_HISTORY_PATH = '/api/v1/macro/notifications'

/** Unused. GET/PUT per-user prediction-alert defaults. */
export const PREDICTION_ALERT_CONFIG_PATH =
  '/api/v1/alerts/prediction/config/{user_id}'
/** Unused. DELETE one event-type subscription. */
export const MACRO_UNSUBSCRIBE_PATH =
  '/api/v1/macro/subscribe/{user_id}/{event_type}'
/** Unused. POST subscribe to every event type. */
export const MACRO_SUBSCRIBE_ALL_PATH = '/api/v1/macro/subscribe-all/{user_id}'
/** Unused. POST drop every event-type subscription. */
export const MACRO_UNSUBSCRIBE_ALL_PATH =
  '/api/v1/macro/unsubscribe-all/{user_id}'
/** Unused. POST a macro alert rule. */
export const MACRO_ALERTS_PATH = '/api/v1/macro/alerts'
/** Unused. GET a user's macro alert rules. */
export const MACRO_ALERTS_BY_USER_PATH = `${MACRO_ALERTS_PATH}/{user_id}`
/** Unused. DELETE one macro alert rule. */
export const MACRO_ALERT_PATH = `${MACRO_ALERTS_PATH}/{alert_id}`
/** Used. PUT mark one macro notification read. The inbox calls this. */
export const MACRO_NOTIFICATION_READ_PATH =
  '/api/v1/macro/notifications/{notification_id}/read'
/** Unused. GET upcoming subscribed events. */
export const MACRO_EVENTS_UPCOMING_PATH = '/api/v1/macro/events/upcoming'

// ---------------------------------------------------------------------------
// AI service
// ---------------------------------------------------------------------------

/** Used. GET BTC forecast. */
export const BTC_PREDICTION_PATH = '/api/v1/predict/btc'
/** Used. GET historical forecast accuracy (the Forecasts accuracy card). */
export const BTC_PREDICTION_PERFORMANCE_PATH = '/api/v1/performance/btc'
/** Used. GET scored forecasts, predicted vs actual (the accuracy card). */
export const BTC_PREDICTION_PERFORMANCE_POINTS_PATH =
  '/api/v1/performance/btc/points'

/** Unused. GET BTC vs macro correlation. */
export const BTC_MACRO_CORRELATION_PATH = '/api/v1/correlation/btc'
/** Unused. GET a generated export file. */
export const AI_EXPORT_PATH = '/api/v1/exports/{file_name}'
/** Unused. GET methodology docs. */
export const AI_METHODOLOGY_PATH = '/api/v1/methodology'
/** Unused. GET methodology versions. */
export const AI_METHODOLOGY_VERSIONS_PATH = '/api/v1/methodology/versions'
/** Unused. GET methodology changelog. */
export const AI_METHODOLOGY_CHANGELOG_PATH = '/api/v1/methodology/changelog'
/** Unused. GET historical events and BTC reaction. */
export const AI_EVENTS_HISTORICAL_PATH = '/api/v1/events/historical'

// ---------------------------------------------------------------------------
// Frontend-only paths — not on the service OpenAPI pages
// ---------------------------------------------------------------------------

/** Used. Price WebSocket the frontend expects on the gateway. */
export const PRICE_STREAM_PATH = '/api/v1/btc/price/stream'
/** Used. In-app inbox. Gateway route is the shared macro notification list. */
export const NOTIFICATIONS_PATH = '/api/v1/macro/notifications'
/** Gateway does not expose an inbox stream. Kept so callers can detect that. */
export const NOTIFICATIONS_STREAM_PATH = `${NOTIFICATIONS_PATH}/stream`

export function priceStreamUrl() {
  return wsUrl(PRICE_STREAM_PATH)
}

export function notificationStreamUrl() {
  return apiUrl(NOTIFICATIONS_STREAM_PATH)
}

/**
 * OpenAPI paths the frontend does not call yet. Import from here when wiring
 * a missing screen so the unused mark can be removed in the same change.
 */
export const unusedApiPaths = {
  dataService: [
    BTC_DOMINANCE_PATH,
    BTC_STATUS_PATH,
    REGIME_BTC_PATH,
    REGIME_BY_ID_PATH,
  ],
  alertService: [
    PREDICTION_ALERT_CONFIG_PATH,
    MACRO_UNSUBSCRIBE_PATH,
    MACRO_SUBSCRIBE_ALL_PATH,
    MACRO_UNSUBSCRIBE_ALL_PATH,
    MACRO_ALERTS_PATH,
    MACRO_ALERTS_BY_USER_PATH,
    MACRO_ALERT_PATH,
    MACRO_EVENTS_UPCOMING_PATH,
  ],
  aiService: [
    BTC_MACRO_CORRELATION_PATH,
    AI_EXPORT_PATH,
    AI_METHODOLOGY_PATH,
    AI_METHODOLOGY_VERSIONS_PATH,
    AI_METHODOLOGY_CHANGELOG_PATH,
    AI_EVENTS_HISTORICAL_PATH,
  ],
} as const
