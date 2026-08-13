import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import { PriceDayStats } from '@/components/dashboard/price/PriceDayStats'

export function renderPriceDayStats(
  high: number | null,
  low: number | null,
  volume: number | null,
) {
  return render(<PriceDayStats high={high} low={low} volume={volume} />)
}

/** Each stat is a `dt`/`dd` pair, so assert the value next to its label. */
export function expectDayStat(label: string, value: string) {
  const term = screen.getByText(label)
  expect(term.nextElementSibling).toHaveTextContent(value)
}
