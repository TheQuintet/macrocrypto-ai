export type NotificationType =
  | 'price_alert'
  | 'prediction_alert'
  | 'confidence_alert'
  | 'macro_alert'

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
