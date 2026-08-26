export type AlertType = 'reaches' | 'crosses_above' | 'crosses_below';
export type AlertStatus = 'active' | 'triggered' | 'disabled' | 'expired';

export interface PriceAlert {
  id: string;
  user_id: string;
  threshold_price: number;
  alert_type: AlertType;
  asset: string;
  status: AlertStatus;
  one_time: boolean;
  created_at: string;
  updated_at: string;
  triggered_at: string | null;
  notify_in_app: boolean;
  notify_email: boolean;
  name: string | null;
  description: string | null;
}

export interface CreatePriceAlertRequest {
  user_id: string;
  threshold_price: number;
  alert_type: AlertType;
  asset?: string;
  one_time?: boolean;
  name?: string;
  description?: string;
  notify_in_app?: boolean;
  notify_email?: boolean;
}

export interface UpdatePriceAlertRequest {
  threshold_price?: number;
  alert_type?: AlertType;
  asset?: string;
  one_time?: boolean;
  name?: string;
  description?: string;
  notify_in_app?: boolean;
  notify_email?: boolean;
  status?: AlertStatus;
}

export interface PriceAlertHistory {
  id: string;
  alert_id: string;
  event_type: string;
  event_source: string;
  triggered_price: number;
  threshold_price: number;
  alert_type: AlertType;
  previous_status: AlertStatus | null;
  new_status: AlertStatus | null;
  triggered_at: string;
  created_at: string;
}

export interface PriceAlertListResponse {
  total: number;
  limit: number;
  offset: number;
  alerts: PriceAlert[];
}

// Notification Types
export interface InAppNotification {
  id: string;
  user_id: string;
  alert_id: string | null;
  title: string;
  message: string;
  notification_type: 'price_alert' | 'prediction_alert' | 'confidence_alert' | 'macro_alert';
  data: Record<string, unknown> | null;
  action_url: string | null;
  read: boolean;
  is_archived: boolean;
  created_at: string;
  read_at: string | null;
}

export interface NotificationResponse {
  total: number;
  limit: number;
  offset: number;
  notifications: InAppNotification[];
}
