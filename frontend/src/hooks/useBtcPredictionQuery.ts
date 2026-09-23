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
  const params: PredictionParams = { horizon, confidence }

  return useQuery<BtcPrediction, Error>({
    queryKey: btcPredictionQueryKey(params),
    queryFn: () => fetchBtcPrediction(params),
    staleTime: PREDICTION_STALE_MS,
    placeholderData: keepPreviousData,
  })
}
