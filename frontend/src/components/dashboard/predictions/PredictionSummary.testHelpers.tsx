import { render, screen, within } from '@testing-library/react'
import { expect } from 'vitest'
import { PredictionSummary } from '@/components/dashboard/predictions/PredictionSummary'
import {
  makePrediction,
  makePredictionPoint,
} from '@/api/predictions/btcPrediction.testHelpers'
import type { BtcPrediction } from '@/types/predictions'

export { makePredictionPoint }

export function renderSummary(overrides: Partial<BtcPrediction> = {}) {
  return render(<PredictionSummary prediction={makePrediction(overrides)} />)
}

function getStat(label: string) {
  return screen.getByRole('group', { name: label })
}

export function expectStat(label: string, value: string | RegExp) {
  expect(within(getStat(label)).getByText(value)).toBeInTheDocument()
}

export function expectTrend(label: string) {
  expect(
    screen.getByLabelText(`Trend ${label.toLowerCase()}`),
  ).toBeInTheDocument()
}

export function expectKeyLevels(high: string, low: string) {
  const levels = screen.getByRole('group', { name: 'Confidence range' })

  expect(within(levels).getByText(high)).toBeInTheDocument()
  expect(within(levels).getByText(low)).toBeInTheDocument()
}

/** The headline forecast, which carries the direction as its colour. */
export function getPredictedPrice(value: string) {
  return screen.getByText(value)
}

export function expectPredictedPriceTone(value: string, tone: string) {
  expect(getPredictedPrice(value)).toHaveClass(tone)
}


export function expectBandWidth(label: string) {
  const indicator = screen.getByRole('group', {
    name: 'Confidence range width',
  })

  expect(within(indicator).getByText(label)).toBeInTheDocument()
}
