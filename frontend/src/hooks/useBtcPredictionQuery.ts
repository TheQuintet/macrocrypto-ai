import { keepPreviousData, useQuery } from '@tanstack/react-query'
import {
  btcPredictionQueryKey,
  fetchBtcPrediction,
  PREDICTION_STALE_MS,
} from '@/api/predictions/btcPrediction'
import { usePredictionStore } from '@/stores/predictionStore'
import type { BtcPrediction, PredictionParams } from '@/types/predictions'

/**
 * Prediction batch for the currently selected horizon and confidence.
 *
 * The previous batch is kept while a new one loads, so switching horizon or
 * confidence redraws the chart in place instead of flashing a skeleton.
 */
export function useBtcPredictionQuery() {
  const horizon = usePredictionStore((state) => state.horizon)
  const confidence = usePredictionStore((state) => state.confidence)

  return useBtcPredictionQueryFor({ horizon, confidence })
}

/**
 * Prediction batch for a fixed horizon and confidence, without reading the
 * Forecasts screen's selection — for views that always show one window.
 *
 * Same key as the selected-window query, so both share one cache entry.
 */
export function useBtcPredictionQueryFor(params: PredictionParams) {
  return useQuery<BtcPrediction, Error>({
    queryKey: btcPredictionQueryKey(params),
    queryFn: () => fetchBtcPrediction(params),
    staleTime: PREDICTION_STALE_MS,
    placeholderData: keepPreviousData,
  })
}
