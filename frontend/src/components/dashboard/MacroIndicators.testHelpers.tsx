import { render, screen } from '@testing-library/react'
import { MacroIndicators } from './MacroIndicators'
import { TooltipProvider } from '@/components/ui/tooltip'
import type { MacroIndicator } from '@/types/macroIndicators'

export const mockIndicators: MacroIndicator[] = [
  {
    indicator_name: 'CPI',
    time: new Date().toISOString(),
    current_value: 307.2,
    previous_value: 306.5,
    change_percent: 0.23,
    trend: '↑',
    source: 'fred',
    dataSource: 'live',
  },
  {
    indicator_name: 'FEDFUNDS',
    time: new Date().toISOString(),
    current_value: 5.5,
    previous_value: 5.5,
    change_percent: 0.0,
    trend: '→',
    source: 'fred',
    dataSource: 'live',
  },
  {
    indicator_name: 'UNEMPLOYMENT',
    time: new Date().toISOString(),
    current_value: 4.1,
    previous_value: 4.2,
    change_percent: -2.38,
    trend: '↓',
    source: 'fred',
    dataSource: 'live',
  },
  {
    indicator_name: 'GDP',
    time: new Date().toISOString(),
    current_value: 32475.21,
    previous_value: 31865.721,
    change_percent: 1.91,
    trend: '↑',
    source: 'fred',
    dataSource: 'live',
  },
]

export function renderMacroIndicators(
  props: Partial<React.ComponentProps<typeof MacroIndicators>> = {},
) {
  return render(
    <TooltipProvider>
      <MacroIndicators
        indicators={mockIndicators}
        isLoading={false}
        error={null}
        {...props}
      />
    </TooltipProvider>,
  )
}

export function getCardByIndicatorName(name: string) {
  const element = screen.getByText(name)
  return element.closest('[data-slot="card"]')
}

export function getChangeElement(card: Element | null | undefined) {
  return card?.querySelector('button')
}
