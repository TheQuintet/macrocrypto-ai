import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { MAIN_INDICATOR_NAMES } from '@/api/macroIndicators'
import { MacroIndicatorHistory } from '@/components/dashboard/indicators/MacroIndicatorHistory'
import {
  expectHistoryCharts,
  expectHistoryTable,
  renderHistory,
} from './MacroIndicatorHistory.testHelpers'

describe('MacroIndicatorHistory', () => {
  afterEach(() => {
    cleanup()
  })

  it('renders a chart per series and a table of observations', () => {
    renderHistory()

    expectHistoryCharts()
    expectHistoryTable()
    expect(screen.getAllByText('321.00').length).toBeGreaterThan(0)
  })

  it('shows loading skeletons when isLoading is true', () => {
    const { container } = render(
      <MacroIndicatorHistory indicators={[]} isLoading />,
    )

    const cards = container.querySelectorAll('[data-slot="card"]')
    expect(cards).toHaveLength(MAIN_INDICATOR_NAMES.length)
  })

  it('shows an error message when the history request fails', () => {
    render(
      <MacroIndicatorHistory
        indicators={[]}
        error={new Error('upstream timeout')}
      />,
    )

    expect(
      screen.getByText('Failed to load historical indicator data'),
    ).toBeInTheDocument()
    expect(screen.getByText('upstream timeout')).toBeInTheDocument()
  })

  it('shows an empty state when there are no observations', () => {
    render(<MacroIndicatorHistory indicators={[]} />)

    expect(
      screen.getByText('No historical indicator data available'),
    ).toBeInTheDocument()
  })
})
