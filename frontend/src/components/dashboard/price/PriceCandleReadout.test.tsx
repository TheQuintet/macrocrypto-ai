import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { PriceCandleReadout } from '@/components/dashboard/price/PriceCandleReadout'
import type { ChartCandle } from '@/types/chart'

const CANDLE: ChartCandle = {
  time: 'Mar 5 14:00',
  timeMs: Date.parse('2024-03-05T14:00:00.000Z'),
  open: 64_000,
  high: 64_400,
  low: 63_900,
  close: 64_100.5,
}

describe('PriceCandleReadout', () => {
  afterEach(() => {
    cleanup()
  })

  it('asks the reader to tap a candle when nothing is selected', () => {
    render(<PriceCandleReadout candle={null} />)

    expect(
      screen.getByText(/tap a candle to see open, high, low, close/i),
    ).toBeInTheDocument()
  })

  it('shows OHLC for the selected candle', () => {
    render(<PriceCandleReadout candle={CANDLE} />)

    const readout = screen.getByRole('region', { name: 'Selected candle' })
    expect(readout).toHaveTextContent('Open')
    expect(readout).toHaveTextContent('$64,000.00')
    expect(readout).toHaveTextContent('Mar 5 14:00')
  })
})
