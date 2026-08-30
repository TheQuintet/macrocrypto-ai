import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { PriceCandleTooltip } from '@/components/dashboard/price/PriceCandleTooltip'
import type { ChartCandle } from '@/types/chart'

const CANDLE: ChartCandle = {
  time: 'Mar 5 14:00',
  timeMs: Date.parse('2024-03-05T14:00:00.000Z'),
  open: 64_000,
  high: 64_400,
  low: 63_900,
  close: 64_100.5,
}

function renderTooltip(active: boolean, candle?: ChartCandle) {
  return render(
    <PriceCandleTooltip
      active={active}
      payload={candle ? [{ payload: candle }] : []}
    />,
  )
}

function expectRow(label: string, value: string) {
  expect(screen.getByText(label).nextElementSibling).toHaveTextContent(value)
}

describe('PriceCandleTooltip', () => {
  afterEach(() => {
    cleanup()
  })

  it('breaks the hovered candle down into OHLC', () => {
    renderTooltip(true, CANDLE)

    expectRow('Open', '$64,000.00')
    expectRow('High', '$64,400.00')
    expectRow('Low', '$63,900.00')
    expectRow('Close', '$64,100.50')
  })

  it('labels the bucket it belongs to', () => {
    renderTooltip(true, CANDLE)

    expect(screen.getByText('Mar 5 14:00')).toBeInTheDocument()
  })

  it('renders nothing while inactive', () => {
    renderTooltip(false, CANDLE)

    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('renders nothing without a hovered candle', () => {
    renderTooltip(true, undefined)

    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('lists as-of macro change instead of raw prints', () => {
    renderTooltip(true, {
      ...CANDLE,
      asOfIndicators: {
        cpi: { value: 322.13, indexed: 101.2, changePercent: 0.21 },
        gdp: { value: 30353.9, indexed: 100.8, changePercent: -0.5 },
      },
    })

    expectRow('cpi', '↑ +0.21%')
    expectRow('gdp', '↓ -0.50%')
    expect(screen.getByText('↑ +0.21%')).toHaveClass('text-negative')
    expect(screen.getByText('↓ -0.50%')).toHaveClass('text-negative')
  })
})
