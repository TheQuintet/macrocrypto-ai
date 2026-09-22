import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import { PredictionTooltip } from '@/components/dashboard/predictions/PredictionTooltip'
import type { PredictionChartRow } from '@/types/predictions'

export function makeForecastRow(
  overrides: Partial<PredictionChartRow> = {},
): PredictionChartRow {
  const timeMs = overrides.timeMs ?? Date.UTC(2024, 5, 15, 13)
  const row: PredictionChartRow = {
    kind: 'forecast',
    time: new Date(timeMs).toISOString(),
    timeMs,
    predicted: 64_000,
    lower: 63_400,
    upper: 64_600,
    ...overrides,
  }

  return { ...row, band: [row.lower!, row.upper!] }
}

export function makeHistoryRow(
  overrides: Partial<PredictionChartRow> = {},
): PredictionChartRow {
  const timeMs = overrides.timeMs ?? Date.UTC(2024, 5, 15, 12)
  const row: PredictionChartRow = {
    kind: 'history',
    time: new Date(timeMs).toISOString(),
    timeMs,
    open: 63_500,
    high: 63_900,
    low: 63_300,
    close: 63_800,
    ...overrides,
  }

  if (row.low == null || row.high == null) {
    return row
  }

  return { ...row, candle: [row.low, row.high] }
}

type RenderTooltipOptions = {
  active?: boolean
  row?: PredictionChartRow
  confidence?: number
  currentPrice?: number | null
}

export function renderTooltip({
  active = true,
  row = makeForecastRow(),
  confidence = 0.85,
  currentPrice = 63_500,
}: RenderTooltipOptions = {}) {
  return render(
    <PredictionTooltip
      active={active}
      payload={[{ payload: row }]}
      confidence={confidence}
      currentPrice={currentPrice}
    />,
  )
}

/** Recharts keeps the tooltip mounted between points, with nothing to show. */
export function renderTooltipWithoutPoint() {
  return render(
    <PredictionTooltip active payload={[]} confidence={0.85} currentPrice={0} />,
  )
}

export function expectTooltipShows(text: string | RegExp) {
  expect(screen.getByText(text)).toBeInTheDocument()
}

export function expectNoTooltip() {
  expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
}

export function expectTooltipMissing(text: string | RegExp) {
  expect(screen.queryByText(text)).not.toBeInTheDocument()
}
