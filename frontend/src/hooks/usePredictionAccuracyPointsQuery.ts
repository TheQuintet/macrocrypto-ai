import { useQuery } from '@tanstack/react-query'
import {
  PREDICTION_ACCURACY_DAYS,
  PREDICTION_ACCURACY_STALE_MS,
} from '@/api/predictions/predictionAccuracy'
import {
  fetchPredictionAccuracyPoints,
  predictionAccuracyPointsQueryKey,
} from '@/api/predictions/predictionAccuracyPoints'
import type {
  PredictionAccuracyPoints,
  PredictionAccuracyPointsParams,
} from '@/types/predictionAccuracy'
import type { PredictionHorizon } from '@/types/predictions'

/**
 * Predicted against actual price for the model the accuracy card grades, so
 * the comparison and the score describe the same forecasts.
 */
export function usePredictionAccuracyPointsQuery(
  horizon: PredictionHorizon,
  modelName: string,
) {
  const params: PredictionAccuracyPointsParams = {
    horizon,
    days: PREDICTION_ACCURACY_DAYS,
    modelName,
  }

  return useQuery<PredictionAccuracyPoints, Error>({
    queryKey: predictionAccuracyPointsQueryKey(params),
    queryFn: () => fetchPredictionAccuracyPoints(params),
    staleTime: PREDICTION_ACCURACY_STALE_MS,
  })
}
