export type PredictionHorizon = '24h' | '7d'
export type PredictionThreshold = 1 | 2 | 5 | 10
export type PredictionDirection = 'up' | 'down' | 'both'
export type PredictionAlertStatus = 'active' | 'disabled' | 'triggered' | 'expired'

export interface PredictionAlert {
  id: string
  user_id: string
  threshold: PredictionThreshold
  horizon: PredictionHorizon
  confidence_change: number
  direction: PredictionDirection
  asset: string
  status: PredictionAlertStatus
  one_time: boolean
  name?: string
  description?: string
  notify_in_app: boolean
  notify_email: boolean
  created_at: string
  updated_at: string
  triggered_at?: string | null
}

/** Wire shape from `GET/POST /api/v1/alerts/prediction/`. */
export interface PredictionAlertApiRecord {
  id: string
  user_id: string
  threshold_percent: number
  horizon: string
  direction: string
  asset: string
  monitor_confidence: boolean
  confidence_threshold_percent: number
  status: string
  created_at: string
  updated_at: string
  triggered_at: string | null
  notify_in_app: boolean
  notify_email: boolean
  name: string | null
  description: string | null
}

export interface PredictionAlertListResponse {
  total: number
  limit: number
  offset: number
  alerts: PredictionAlertApiRecord[]
}

export interface CreatePredictionAlertRequest {
  user_id: string;
  threshold: PredictionThreshold;
  horizon: PredictionHorizon;
  confidence_change: number;
  one_time: boolean;
  direction?: PredictionDirection;
  name?: string;
  description?: string;
  notify_in_app: boolean;
  notify_email: boolean;
}

export interface UpdatePredictionAlertRequest {
  threshold?: PredictionThreshold;
  horizon?: PredictionHorizon;
  confidence_change?: number;
  one_time?: boolean;
  direction?: PredictionDirection;
  name?: string;
  description?: string;
  notify_in_app?: boolean;
  notify_email?: boolean;
  status?: PredictionAlertStatus;
}

export interface PredictionAlertHistory {
  id: string;
  alert_id: string;
  previous_prediction: number;
  new_prediction: number;
  change_percentage: number;
  horizon: PredictionHorizon;
  threshold: PredictionThreshold;
  triggered_at: string;
  recommendation: string;
  read: boolean;
}
