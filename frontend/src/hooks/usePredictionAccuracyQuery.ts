import { keepPreviousData, useQuery } from '@tanstack/react-query'
import {
  fetchPredictionAccuracy,
  PREDICTION_ACCURACY_DAYS,
  PREDICTION_ACCURACY_STALE_MS,
  predictionAccuracyQueryKey,
} from '@/api/predictions/predictionAccuracy'
import { usePredictionStore } from '@/stores/predictionStore'
import type {
  PredictionAccuracy,
  PredictionAccuracyParams,
} from '@/types/predictionAccuracy'

/**
 * Historical accuracy for the horizon selected on the forecast chart, so the
 * card always grades the same window the trader is looking at.
 */
export function usePredictionAccuracyQuery() {
  const horizon = usePredictionStore((state) => state.horizon)
  const params: PredictionAccuracyParams = {
    horizon,
    days: PREDICTION_ACCURACY_DAYS,
  }

  return useQuery<PredictionAccuracy | null, Error>({
    queryKey: predictionAccuracyQueryKey(params),
    queryFn: () => fetchPredictionAccuracy(params),
    staleTime: PREDICTION_ACCURACY_STALE_MS,
    placeholderData: keepPreviousData,
  })
}
