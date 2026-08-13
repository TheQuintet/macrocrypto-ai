import { screen, waitFor } from '@testing-library/react'
import { expect, vi } from 'vitest'
import { BtcPriceCard } from '@/components/dashboard/price/BtcPriceCard'
import { TooltipProvider } from '@/components/ui/tooltip'
import { renderWithQuery } from '@/test/renderWithQuery'
import type { BtcPriceSnapshot } from '@/types/btcPrice'

export const SNAPSHOT: BtcPriceSnapshot = {
  currentPrice: 64_213.5,
  change24h: 1_113.5,
  change24hPercent: 1.76,
  high24h: 64_993.5,
  low24h: 63_573.5,
  volume24h: 24_180.42,
  change7d: 2_813.5,
  change7dPercent: 4.58,
  updatedAt: '2024-06-15T12:00:00.000Z',
}

export function snapshotWith(
  overrides: Partial<BtcPriceSnapshot>,
): BtcPriceSnapshot {
  return { ...SNAPSHOT, ...overrides }
}

export function renderBtcPriceCard() {
  // AppLayout provides the tooltip context in the app; mirror it here.
  return renderWithQuery(
    <TooltipProvider>
      <BtcPriceCard />
    </TooltipProvider>,
  )
}

export async function expectPriceShown(text: string) {
  await waitFor(() => {
    expect(screen.getByText(text)).toBeInTheDocument()
  })
}

export function expectLoadingSkeleton() {
  expect(document.querySelectorAll('[data-slot="skeleton"]').length).toBeGreaterThan(0)
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
}

export async function expectPriceUnavailable() {
  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent(/price unavailable/i)
  })
}

export async function expect24hSessionShown() {
  await waitFor(() => {
    expect(screen.getByText('24h high').nextElementSibling).toHaveTextContent(
      '$64,993.50',
    )
  })
  expect(screen.getByText('24h low').nextElementSibling).toHaveTextContent(
    '$63,573.50',
  )
  expect(screen.getByText('24h volume').nextElementSibling).toHaveTextContent(
    '24,180.42 BTC',
  )
}

/** Silence the expected console noise from a rejected query. */
export function silenceQueryErrors() {
  return vi.spyOn(console, 'error').mockImplementation(() => undefined)
}
