import { render } from '@testing-library/react'
import { expect } from 'vitest'
import { MacroIndicatorHistoryTable } from '@/components/dashboard/indicators/MacroIndicatorHistoryTable'
import { TooltipProvider } from '@/components/ui/tooltip'
import { makeIndicator } from '@/api/macroIndicators.testHelpers'
import { indicatorSeriesColor } from '@/lib/indicatorSeriesColor'
import { mockHistoryIndicators } from './MacroIndicatorHistory.testHelpers'

export function renderHistoryTable() {
  return render(
    <TooltipProvider>
      <MacroIndicatorHistoryTable
        indicators={[
          ...mockHistoryIndicators,
          makeIndicator({
            indicator_name: 'federal_funds_rate',
            time: '2026-08-01T00:00:00.000Z',
            current_value: 4.33,
            change_percent: 0,
          }),
        ]}
      />
    </TooltipProvider>,
  )
}

export function expectRowUsesSeriesColor(name: string) {
  const rows = document.querySelectorAll(`[data-indicator="${name}"]`)
  expect(rows.length).toBeGreaterThan(0)

  const color = indicatorSeriesColor(name)
  for (const node of rows) {
    expect(node).toHaveStyle({ borderLeftColor: color })
    expect(node.querySelector('span.uppercase')).toHaveStyle({ color })
  }
}
