export type NotificationType =
  | 'price_alert'
  | 'prediction_alert'
  | 'confidence_alert'
  | 'macro_alert'

/** Query params for GET /api/v1/macro/notifications (and simulated inbox list). */
export interface NotificationListParams {
  unread_only?: boolean
  limit?: number
  offset?: number
}

/** One list item from GET /api/v1/macro/notifications before mapping to the inbox model. */
export interface MacroNotificationWire {
  id: string
  user_id?: string
  alert_id?: string | null
  event_name?: string
  description?: string | null
  data?: Record<string, unknown> | null
  action_url?: string | null
  read?: boolean
  is_archived?: boolean
  sent_at?: string | null
  read_at?: string | null
  title?: string
  message?: string
  notification_type?: NotificationType
  created_at?: string
}

/** Paginated gateway body from GET /api/v1/macro/notifications. */
export interface MacroNotificationListResponse {
  total: number
  limit: number
  offset: number
  notifications: MacroNotificationWire[]
}

export interface InAppNotification {
  id: string
  user_id: string
  alert_id: string | null
  title: string
  message: string
  notification_type: NotificationType
  data: Record<string, unknown> | null
  action_url: string | null
  read: boolean
  is_archived: boolean
  created_at: string
  read_at: string | null
}

export interface NotificationResponse {
  total: number
  limit: number
  offset: number
  notifications: InAppNotification[]
}
