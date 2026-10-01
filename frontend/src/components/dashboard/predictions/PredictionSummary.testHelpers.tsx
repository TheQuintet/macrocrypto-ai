import { render, screen, within } from '@testing-library/react'
import { expect } from 'vitest'
import { PredictionSummary } from '@/components/dashboard/predictions/PredictionSummary'
import {
  makePrediction,
  makePredictionPoint,
} from '@/api/predictions/btcPrediction.testHelpers'
import { PREDICTION_CONFIDENCE_OPTIONS } from '@/stores/predictionStore'
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

/**
 * The meter reads the level as the range it covers, in one neutral colour —
 * not as a green "High" or a red "Low".
 */
export function expectRangeCoverage(percent: string) {
  const meter = screen.getByRole('meter', { name: 'Range coverage' })

  expect(screen.getByText(`${percent} range`)).toBeInTheDocument()
  expect(
    screen.getByText(
      new RegExp(`Price expected inside the band ${percent} of the time`),
    ),
  ).toBeInTheDocument()
  expect(meter.firstElementChild).toHaveStyle({ width: percent })
  expect(meter.firstElementChild).toHaveClass('bg-chart-1')
}

/** The old meter read `70% Low` / `95% High`; nothing grades the level now. */
export function expectNoConfidenceGrade() {
  expect(screen.queryByText(/\d+% (High|Moderate|Low)$/)).toBeNull()
}

export function expectCoverageLevels() {
  const scale = screen.getByRole('list', { name: 'Coverage levels' })

  for (const option of PREDICTION_CONFIDENCE_OPTIONS) {
    expect(within(scale).getByText(option.label)).toBeInTheDocument()
  }
}
