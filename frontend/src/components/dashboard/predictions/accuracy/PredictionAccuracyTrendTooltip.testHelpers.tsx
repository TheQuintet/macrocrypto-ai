import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import { PredictionAccuracyTrendTooltip } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyTrendTooltip'
import type { AccuracyTrendRow } from '@/types/predictionAccuracy'

const LINES = [
  { horizon: '24h', swatchClass: 'bg-positive' },
  { horizon: '7d', swatchClass: 'bg-chart-4' },
] as const

export function renderTrendTooltip(row: Partial<AccuracyTrendRow> = {}) {
  return render(
    <PredictionAccuracyTrendTooltip
      active
      payload={[
        {
          payload: {
            timeMs: Date.UTC(2026, 8, 14, 6),
            '24h': 98.2,
            '7d': 89.4,
            ...row,
          },
        },
      ]}
      lines={[...LINES]}
    />,
  )
}

export function expectTrendTooltipShows(text: string | RegExp) {
  expect(screen.getByRole('tooltip')).toHaveTextContent(text)
}
