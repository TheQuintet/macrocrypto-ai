import { render, screen, within } from '@testing-library/react'
import { expect } from 'vitest'
import { PredictionConfidenceScale } from '@/components/dashboard/predictions/PredictionConfidenceScale'
import { PREDICTION_CONFIDENCE_OPTIONS } from '@/stores/predictionStore'

export function renderPredictionConfidenceScale(confidence = 0.85) {
  return render(<PredictionConfidenceScale confidence={confidence} />)
}

function getScale() {
  return screen.getByRole('list', { name: 'Coverage levels' })
}

export function expectPredictionConfidenceScaleKey() {
  for (const option of PREDICTION_CONFIDENCE_OPTIONS) {
    expect(within(getScale()).getByText(option.label)).toBeInTheDocument()
  }
}

export function expectCoverageLevelSelected(label: string) {
  expect(within(getScale()).getByText(label)).toHaveAttribute(
    'aria-current',
    'true',
  )
}

/** One colour for every level: none is styled as better than another. */
export function expectNoGradedTone() {
  for (const item of within(getScale()).getAllByRole('listitem')) {
    expect(item.className).not.toMatch(/positive|negative|warning/)
  }
}
