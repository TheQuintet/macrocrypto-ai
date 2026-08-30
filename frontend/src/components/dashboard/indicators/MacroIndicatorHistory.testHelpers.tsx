import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import { MacroIndicatorHistory } from '@/components/dashboard/indicators/MacroIndicatorHistory'
import { TooltipProvider } from '@/components/ui/tooltip'
import { makeIndicator } from '@/api/macroIndicators/macroIndicators.testHelpers'
import type { MacroIndicator } from '@/types/macroIndicators'

export const mockHistoryIndicators: MacroIndicator[] = [
  makeIndicator({
    indicator_name: 'cpi',
    time: '2026-05-01T00:00:00.000Z',
    current_value: 320.1,
    previous_value: 319.4,
    change_percent: 0.22,
    trend: '↑',
  }),
  makeIndicator({
    indicator_name: 'cpi',
    time: '2026-06-01T00:00:00.000Z',
    current_value: 321.0,
    previous_value: 320.1,
    change_percent: 0.28,
    trend: '↑',
  }),
  makeIndicator({
    indicator_name: 'gdp',
    time: '2026-04-01T00:00:00.000Z',
    current_value: 30100,
    previous_value: 29800,
    change_percent: 1.01,
    trend: '↑',
  }),
  makeIndicator({
    indicator_name: 'gdp',
    time: '2026-07-01T00:00:00.000Z',
    current_value: 30353.9,
    previous_value: 30100,
    change_percent: 0.84,
    trend: '↑',
  }),
]

export function renderHistory(
  props: Partial<React.ComponentProps<typeof MacroIndicatorHistory>> = {},
) {
  return render(
    <TooltipProvider>
      <MacroIndicatorHistory
        indicators={mockHistoryIndicators}
        isLoading={false}
        error={null}
        {...props}
      />
    </TooltipProvider>,
  )
}

export function expectHistoryCharts() {
  expect(
    screen.getByRole('img', { name: /macro indicator history/i }),
  ).toBeInTheDocument()
}

export function expectHistoryTable() {
  expect(
    screen.getByRole('region', { name: /historical indicator observations/i }),
  ).toBeInTheDocument()
}
