import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { MAIN_INDICATOR_NAMES } from '@/api/macroIndicators'
import { indicatorSeriesColor } from '@/lib/indicatorSeriesColor'
import { MacroIndicators } from './MacroIndicators'
import {
  getCardByIndicatorName,
  renderMacroIndicators,
} from './MacroIndicators.testHelpers'

describe('MacroIndicators', () => {
  afterEach(() => {
    cleanup()
  })

  it('renders all indicators with their values', () => {
    renderMacroIndicators()

    expect(screen.getByText('CPI')).toBeInTheDocument()
    expect(screen.getByText('FEDFUNDS')).toBeInTheDocument()
    expect(screen.getByText('UNEMPLOYMENT')).toBeInTheDocument()
    expect(screen.getByText('GDP')).toBeInTheDocument()

    expect(screen.getAllByText('307.20')[0]).toBeInTheDocument()
    expect(screen.getAllByText('5.50')[0]).toBeInTheDocument()
    expect(screen.getAllByText('4.10')[0]).toBeInTheDocument()
    expect(screen.getAllByText('32475.21')[0]).toBeInTheDocument()
  })

  it('colors each known series card to match the chart tokens', () => {
    renderMacroIndicators()

    for (const name of ['CPI', 'GDP'] as const) {
      const card = getCardByIndicatorName(name)
      const color = indicatorSeriesColor(name)
      expect(card).toHaveStyle({ borderLeftColor: color })
      expect(card?.querySelector('[data-slot="card-title"]')).toHaveStyle({
        color,
      })
    }
  })

  it('uses a single-column grid so cards stack on small screens', () => {
    const { container } = renderMacroIndicators()
    const grid = container.querySelector('.grid')
    expect(grid).toHaveClass('grid-cols-1')
  })

  it('displays previous values correctly', () => {
    renderMacroIndicators()

    const prevValues = screen.getAllByText(/306.50/)
    expect(prevValues.length).toBeGreaterThan(0)

    const prevFedFunds = screen.getAllByText(/5.50/)
    expect(prevFedFunds.length).toBeGreaterThan(0)
  })

  it('shows loading skeletons when isLoading is true', () => {
    const { container } = render(
      <MacroIndicators indicators={[]} isLoading={true} />,
    )

    const cards = container.querySelectorAll('[data-slot="card"]')
    expect(cards).toHaveLength(MAIN_INDICATOR_NAMES.length)

    const skeletons = container.querySelectorAll('[data-slot="skeleton"]')
    expect(skeletons.length).toBeGreaterThan(0)
    expect(
      container.querySelectorAll('[data-slot="skeleton"].bg-muted').length,
    ).toBeGreaterThan(0)
  })

  it('shows error message when error is provided', () => {
    const error = new Error('Failed to fetch data')
    render(<MacroIndicators indicators={[]} error={error} />)
    expect(
      screen.getByText('Failed to load macroeconomic indicators'),
    ).toBeInTheDocument()
  })

  it('shows empty state when no indicators are provided', () => {
    render(<MacroIndicators indicators={[]} />)
    expect(
      screen.getByText('No macroeconomic data available'),
    ).toBeInTheDocument()
  })

  it('displays trend arrows with percentage change', () => {
    renderMacroIndicators()

    expect(screen.getAllByText(/↑ \+0\.23%/)[0]).toBeInTheDocument()
    expect(screen.getAllByText(/→ 0\.00%/)[0]).toBeInTheDocument()
    expect(screen.getAllByText(/↓ -2\.38%/)[0]).toBeInTheDocument()
    expect(screen.getAllByText(/↑ \+1\.91%/)[0]).toBeInTheDocument()
  })

  it('displays change indicators with BTC-positive/negative colors', () => {
    renderMacroIndicators()

    expect(screen.getByLabelText(/\+0\.23%, Negative for BTC/)).toHaveClass(
      'text-negative',
    )
    expect(screen.getByLabelText(/\+1\.91%, Positive for BTC/)).toHaveClass(
      'text-positive',
    )
    expect(screen.getByLabelText(/-2\.38%, Positive for BTC/)).toHaveClass(
      'text-positive',
    )
    expect(screen.getByLabelText(/0\.00%, Neutral/)).toHaveClass(
      'text-muted-foreground',
    )
  })
})
