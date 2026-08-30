import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
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

  it('renders a combined chart, legend, and a table of observations', () => {
    renderHistory()

    expectHistoryCharts()
    expectHistoryTable()
    expect(screen.getAllByText('321.00').length).toBeGreaterThan(0)
  })

  it('can render the chart without the observations table', () => {
    renderHistory({ includeTable: false })

    expectHistoryCharts()
    expect(
      screen.queryByRole('region', {
        name: /historical indicator observations/i,
      }),
    ).not.toBeInTheDocument()
  })

  it('can drop the inner card when nested in a shared panel', () => {
    const { container } = renderHistory({ includeTable: false, framed: false })

    expectHistoryCharts()
    expect(container.querySelectorAll('[data-slot="card"]')).toHaveLength(0)
  })

  it('shows loading skeletons when isLoading is true', () => {
    const { container } = render(
      <MacroIndicatorHistory indicators={[]} isLoading />,
    )

    const cards = container.querySelectorAll('[data-slot="card"]')
    expect(cards).toHaveLength(1)
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
