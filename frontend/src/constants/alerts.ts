/** Temporary until auth lands — the seed user that has alerts. */
export const ALERTS_USER_ID = 'b5e2102c-c4ac-46f9-95c3-2a3c389399a9';

// Prediction alert defaults
export const PREDICTION_ALERT_DEFAULTS = {
  DEFAULT_THRESHOLD: 5 as const,
  DEFAULT_HORIZON: '24h' as const,
  MIN_CONFIDENCE_CHANGE: 1,
  MAX_CONFIDENCE_CHANGE: 10,
} as const;

// Alert notification types
export const NOTIFICATION_TYPES = {
  PRICE_ALERT: 'price_alert',
  MACRO_ALERT: 'macro_alert',
  PREDICTION_ALERT: 'prediction_alert',
  CONFIDENCE_ALERT: 'confidence_alert',
} as const;

export type NotificationType = typeof NOTIFICATION_TYPES[keyof typeof NOTIFICATION_TYPES];

// Toast notification durations
export const TOAST_DURATIONS = {
  SUCCESS: 4000,
  ERROR: 5000,
  INFO: 3000,
  NOTIFICATION: 120000, // 2 minutes
} as const;

// API endpoints
export const API_ENDPOINTS = {
  PREDICTION_ALERTS: '/api/alerts/prediction',
  PREDICTION_HISTORY: '/api/alerts/prediction/history',
  PREDICTION_EXPORT: '/api/alerts/prediction/history/export',
  PREDICTION_PREVIEW: '/api/alerts/prediction/preview',
  PRICE_ALERTS: '/api/alerts/price',
  MACRO_ALERTS: '/api/alerts/macro',
  NOTIFICATIONS: '/api/notifications',
} as const;