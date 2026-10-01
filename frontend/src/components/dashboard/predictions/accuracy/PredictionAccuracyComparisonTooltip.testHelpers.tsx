import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import { PredictionAccuracyComparisonTooltip } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyComparisonTooltip'
import type { PredictionAccuracyPoint } from '@/types/predictionAccuracy'

export function makeComparisonPoint(
  overrides: Partial<PredictionAccuracyPoint> = {},
): PredictionAccuracyPoint {
  const timeMs = Date.UTC(2026, 8, 14, 6)
  return {
    time: new Date(timeMs).toISOString(),
    timeMs,
    predicted: 64_100.5,
    actual: 63_880.2,
    marketCondition: 'bull',
    ...overrides,
  }
}

export function renderComparisonTooltip(point = makeComparisonPoint()) {
  return render(
    <PredictionAccuracyComparisonTooltip active payload={[{ payload: point }]} />,
  )
}

export function renderInactiveComparisonTooltip() {
  return render(
    <PredictionAccuracyComparisonTooltip
      active={false}
      payload={[{ payload: makeComparisonPoint() }]}
    />,
  )
}

export function expectComparisonTooltipShows(text: string | RegExp) {
  expect(screen.getByRole('tooltip')).toHaveTextContent(text)
}

export function expectComparisonTooltipOmits(text: string | RegExp) {
  expect(screen.getByRole('tooltip')).not.toHaveTextContent(text)
}

export function expectNoComparisonTooltip() {
  expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
}
