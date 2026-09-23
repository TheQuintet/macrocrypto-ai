import { keepPreviousData, useQuery } from '@tanstack/react-query'
import {
  fetchPredictionHistory,
  historyParamsFor,
  predictionHistoryQueryKey,
} from '@/api/predictions/predictionHistory'
import { PREDICTION_STALE_MS } from '@/api/predictions/btcPrediction'
import { usePredictionStore } from '@/stores/predictionStore'
import type { PredictionHistory } from '@/types/predictions'

/**
 * Actual candles for the window behind the selected forecast.
 *
 * Confidence does not change the past, so this is keyed on the horizon alone
 * and stays cached while the confidence selector moves.
 */
export function useBtcPredictionHistoryQuery() {
  const horizon = usePredictionStore((state) => state.horizon)
  const params = historyParamsFor(horizon)

  return useQuery<PredictionHistory, Error>({
    queryKey: predictionHistoryQueryKey(params),
    queryFn: () => fetchPredictionHistory(params),
    staleTime: PREDICTION_STALE_MS,
    placeholderData: keepPreviousData,
  })
}
