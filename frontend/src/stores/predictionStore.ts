import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { zoomPredictionStep } from '@/components/dashboard/lib/predictionZoom'
import type {
  PredictionConfidence,
  PredictionHorizon,
} from '@/types/predictions'

export const PREDICTION_HORIZON_OPTIONS: {
  value: PredictionHorizon
  label: string
}[] = [
  { value: '24h', label: '24h' },
  { value: '7d', label: '7d' },
]

export const PREDICTION_CONFIDENCE_OPTIONS: {
  value: PredictionConfidence
  label: string
}[] = [
  { value: 0.7, label: '70%' },
  { value: 0.85, label: '85%' },
  { value: 0.95, label: '95%' },
]

type PredictionState = {
  horizon: PredictionHorizon
  setHorizon: (horizon: PredictionHorizon) => void
  confidence: PredictionConfidence
  setConfidence: (confidence: PredictionConfidence) => void
  /** Steps of extra history beyond the forecast's own window. */
  historyZoom: number
  zoomHistory: (direction: 'in' | 'out') => void
}

/**
 * View preferences for the Forecasts screen. The forecast data itself is
 * server state and belongs to TanStack Query, not here.
 */
export const usePredictionStore = create<PredictionState>()(
  devtools(
    (set) => ({
      horizon: '24h',
      /** A new horizon re-anchors the window, so the zoom starts over. */
      setHorizon: (horizon) =>
        set({ horizon, historyZoom: 0 }, undefined, 'prediction/setHorizon'),
      confidence: 0.85,
      setConfidence: (confidence) =>
        set({ confidence }, undefined, 'prediction/setConfidence'),
      historyZoom: 0,
      zoomHistory: (direction) =>
        set(
          (state) => ({
            historyZoom: zoomPredictionStep(state.historyZoom, direction),
          }),
          undefined,
          'prediction/zoomHistory',
        ),
    }),
    { name: 'PredictionStore' },
  ),
)
