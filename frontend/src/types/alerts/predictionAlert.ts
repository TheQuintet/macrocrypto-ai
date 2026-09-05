export type PredictionHorizon = '24h' | '7d';
export type PredictionThreshold = 1 | 2 | 5 | 10;

export interface PredictionAlert {
  id: string;
  user_id: string;
  threshold: PredictionThreshold;
  horizon: PredictionHorizon;
  confidence_change: number;
  status: 'active' | 'disabled' | 'triggered' | 'expired';
  one_time: boolean;
  name?: string;
  description?: string;
  notify_in_app: boolean;
  notify_email: boolean;
  created_at: string;
  updated_at: string;
  triggered_at?: string;
  preview?: PredictionAlertPreview;
}

export interface PredictionAlertPreview {
  previousPrediction: number;
  newPrediction: number;
  changePercentage: number;
  confidence: number;
  recommendation: string;
  horizon: PredictionHorizon;
}

export interface CreatePredictionAlertRequest {
  user_id: string;
  threshold: PredictionThreshold;
  horizon: PredictionHorizon;
  confidence_change: number;
  one_time: boolean;
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
  name?: string;
  description?: string;
  notify_in_app?: boolean;
  notify_email?: boolean;
  status?: 'active' | 'disabled' | 'triggered' | 'expired';
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
