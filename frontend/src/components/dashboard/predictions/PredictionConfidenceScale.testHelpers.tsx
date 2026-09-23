import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import { PredictionConfidenceScale } from '@/components/dashboard/predictions/PredictionConfidenceScale'
import {
  PREDICTION_CONFIDENCE_BAND_ORDER,
  formatPredictionConfidenceBand,
  formatPredictionConfidenceBandRange,
} from '@/components/dashboard/lib/predictionConfidence'

export function renderPredictionConfidenceScale() {
  return render(<PredictionConfidenceScale />)
}

export function expectPredictionConfidenceScaleKey() {
  for (const band of PREDICTION_CONFIDENCE_BAND_ORDER) {
    expect(
      screen.getByText(
        `${formatPredictionConfidenceBand(band)} ${formatPredictionConfidenceBandRange(band)}`,
      ),
    ).toBeInTheDocument()
  }
}
