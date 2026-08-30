import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { PriceCandleDetails } from '@/components/dashboard/price/PriceCandleDetails'
import type { ChartCandle } from '@/types/chart'

function candle(overrides: Partial<ChartCandle> = {}): ChartCandle {
  return {
    time: 'Mar 5 14:00',
    timeMs: Date.parse('2024-03-05T14:00:00.000Z'),
    open: 64_000,
    high: 64_400,
    low: 63_900,
    close: 64_100.5,
    ...overrides,
  }
}

describe('PriceCandleDetails', () => {
  afterEach(() => {
    cleanup()
  })

  it('colors open and close green on a bullish candle', () => {
    render(<PriceCandleDetails candle={candle()} />)

    expect(screen.getByText('Bullish').parentElement).toHaveClass('text-positive')
    expect(screen.getByText('$64,000.00')).toHaveClass('text-positive')
    expect(screen.getByText('$64,100.50')).toHaveClass('text-positive')
    expect(screen.getByLabelText('↑ +0.63% from open')).toHaveClass(
      'text-positive',
    )
    expect(screen.getByLabelText('↓ -0.31% from close')).toHaveClass(
      'text-negative',
    )
  })

  it('colors open and close red on a bearish candle', () => {
    render(
      <PriceCandleDetails
        candle={candle({ open: 64_100, close: 64_000, high: 64_200, low: 63_900 })}
      />,
    )

    expect(screen.getByText('Bearish').parentElement).toHaveClass('text-negative')
    expect(screen.getByText('$64,100.00')).toHaveClass('text-negative')
    expect(screen.getByText('$64,000.00')).toHaveClass('text-negative')
    expect(screen.getByLabelText(/from open/)).toHaveTextContent('↑ +0.16%')
    expect(screen.getByLabelText(/from close/)).toHaveTextContent('↓ -0.16%')
  })

  it('shows as-of indicator change instead of the raw print', () => {
    render(
      <PriceCandleDetails
        candle={candle({
          asOfIndicators: {
            cpi: { value: 322.13, indexed: 101.2, changePercent: 0.21 },
            gdp: { value: 30_353.9, indexed: 99.5, changePercent: -0.5 },
          },
        })}
      />,
    )

    expect(screen.getByText('cpi').nextElementSibling).toHaveTextContent(
      '↑ +0.21%',
    )
    expect(screen.getByText('cpi').nextElementSibling).toHaveClass(
      'text-negative',
    )
    expect(screen.getByText('gdp').nextElementSibling).toHaveClass(
      'text-negative',
    )
    expect(screen.getByText('gdp').nextElementSibling).toHaveTextContent(
      '↓ -0.50%',
    )
    expect(screen.queryByText('322.13')).not.toBeInTheDocument()
  })

  it('colors as-of change by BTC impact, not by whether the print went up', () => {
    render(
      <PriceCandleDetails
        candle={candle({
          asOfIndicators: {
            cpi: { value: 322.13, indexed: 101.2, changePercent: 0.21 },
            gdp: { value: 30_353.9, indexed: 101.5, changePercent: 1.91 },
          },
        })}
      />,
    )

    expect(screen.getByText('cpi').nextElementSibling).toHaveClass(
      'text-negative',
    )
    expect(screen.getByText('gdp').nextElementSibling).toHaveClass(
      'text-positive',
    )
  })
})
