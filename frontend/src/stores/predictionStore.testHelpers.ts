import { act } from '@testing-library/react'
import { usePredictionStore } from '@/stores/predictionStore'
import type {
  PredictionConfidence,
  PredictionHorizon,
} from '@/types/predictions'

export function resetPredictionStore() {
  act(() => {
    usePredictionStore.setState({
      horizon: '24h',
      confidence: 0.85,
      historyZoom: 0,
    })
  })
}

export function setStoreHorizon(horizon: PredictionHorizon) {
  act(() => {
    usePredictionStore.getState().setHorizon(horizon)
  })
}

export function setStoreConfidence(confidence: PredictionConfidence) {
  act(() => {
    usePredictionStore.getState().setConfidence(confidence)
  })
}
