import { useQuery } from '@tanstack/react-query'
import {
  fetchPredictionAccuracy,
  PREDICTION_ACCURACY_DAYS,
  PREDICTION_ACCURACY_STALE_MS,
  predictionAccuracyQueryKey,
} from '@/api/predictions/predictionAccuracy'
import type {
  PredictionAccuracy,
  PredictionAccuracyParams,
} from '@/types/predictionAccuracy'
import type { PredictionHorizon } from '@/types/predictions'

/**
 * Historical accuracy for one horizon. The card asks for both: the trend
 * always draws 24h and 7d together, and the chart toggle then switches the
 * rest of the card instantly. Each horizon is cached on its own.
 */
export function usePredictionAccuracyQuery(horizon: PredictionHorizon) {
  const params: PredictionAccuracyParams = {
    horizon,
    days: PREDICTION_ACCURACY_DAYS,
  }

  return useQuery<PredictionAccuracy | null, Error>({
    queryKey: predictionAccuracyQueryKey(params),
    queryFn: () => fetchPredictionAccuracy(params),
    staleTime: PREDICTION_ACCURACY_STALE_MS,
  })
}
