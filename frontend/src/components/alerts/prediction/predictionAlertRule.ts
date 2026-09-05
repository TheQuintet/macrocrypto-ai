import type { PredictionHorizon, PredictionThreshold } from '@/types/alerts/predictionAlert';

export const HORIZON_LABELS: Record<PredictionHorizon, string> = {
  '24h': '24 hours',
  '7d': '7 days',
};

export const HORIZON_SHORT_LABELS: Record<PredictionHorizon, string> = {
  '24h': '24h',
  '7d': '7d',
};

export const THRESHOLD_OPTIONS: PredictionThreshold[] = [1, 2, 5, 10];

export const THRESHOLD_LABELS: Record<PredictionThreshold, string> = {
  1: '1%',
  2: '2%',
  5: '5%',
  10: '10%',
};

export const DEFAULT_CONFIDENCE_CHANGE = 5;

export function formatPredictionAlertHeadline(
  threshold: PredictionThreshold,
  horizon: PredictionHorizon,
): string {
  return `Prediction changes by ${THRESHOLD_LABELS[threshold]} or more (${HORIZON_SHORT_LABELS[horizon]})`;
}

export function getRecommendation(
  previousPrediction: number,
  newPrediction: number,
): string {
  const diff = newPrediction - previousPrediction;
  const absDiff = Math.abs(diff);

  if (absDiff < 0.5) return 'Minor change detected';
  if (absDiff < 2) return 'Consider monitoring';

  if (diff > 0) {
    return 'Bullish shift - consider increasing exposure';
  }
  return 'Bearish shift - consider adjusting position';
}

export function formatConfidenceDisplay(confidence: number): string {
  return `${confidence.toFixed(0)}%`;
}
