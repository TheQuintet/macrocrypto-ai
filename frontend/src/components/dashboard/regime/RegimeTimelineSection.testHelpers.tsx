import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { RegimeTimelineSection } from '@/components/dashboard/regime/RegimeTimelineSection'
import { TooltipProvider } from '@/components/ui/tooltip'
import { renderWithQuery } from '@/test/renderWithQuery'
import type { RegimeHistory, RegimeHistoryRow } from '@/types/regime'

export function historyRow(
  overrides: Partial<RegimeHistoryRow> = {},
): RegimeHistoryRow {
  return {
    id: 4,
    regimeType: 'growth',
    startDate: '2023-08-01',
    endDate: '2024-02-29',
    isCurrent: false,
    performance: {
      avgReturn: 28.4,
      maxDrawdown: -11.2,
      volatility: 36.8,
      sharpeRatio: 1.42,
      btcPriceStart: 47_800,
      btcPriceEnd: 61_400,
    },
    ...overrides,
  }
}

export const CURRENT_ROW = historyRow({
  id: 5,
  regimeType: 'rising_rates',
  startDate: '2024-03-01',
  endDate: null,
  isCurrent: true,
  performance: null,
})

export function history(
  rows: RegimeHistoryRow[],
  source: RegimeHistory['source'] = 'live',
): RegimeHistory {
  return { source, rows }
}

export function renderRegimeTimeline() {
  // AppLayout provides the tooltip context in the app; mirror it here.
  return renderWithQuery(
    <TooltipProvider>
      <RegimeTimelineSection />
    </TooltipProvider>,
  )
}

function segmentFor(regimeType: string) {
  const segment = document.querySelector(
    '[data-regime="' + regimeType + '"]',
  )

  expect(segment).not.toBeNull()
  return segment as HTMLElement
}

export async function expectSegmentShown(regimeType: string) {
  await waitFor(() => {
    expect(segmentFor(regimeType)).toBeInTheDocument()
  })
}

export function expectSegmentCount(count: number) {
  expect(document.querySelectorAll('[data-regime]')).toHaveLength(count)
}

/** Width is the regime's share of the band, so it encodes duration. */
export function expectSegmentWiderThan(wider: string, narrower: string) {
  const width = (regimeType: string) =>
    Number.parseFloat(segmentFor(regimeType).style.width)

  expect(width(wider)).toBeGreaterThan(width(narrower))
}

export function expectCurrentHighlight(regimeType: string) {
  expect(segmentFor(regimeType)).toHaveAttribute('data-current', 'true')
}

export function expectNoCurrentHighlight(regimeType: string) {
  expect(segmentFor(regimeType)).not.toHaveAttribute('data-current')
}

export function expectYearTick(label: string) {
  expect(screen.getByText(label)).toBeInTheDocument()
}

export async function clickSegment(regimeType: string) {
  await userEvent.click(segmentFor(regimeType))
}

export async function expectDetailsDialog(title: string) {
  await waitFor(() => {
    expect(screen.getByRole('dialog')).toHaveTextContent(title)
  })
}

export function expectNoDetailsDialog() {
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
}

export function zoomLevel() {
  return screen.getByText(/^\d+x$/).textContent
}

export async function clickZoomIn() {
  await userEvent.click(
    screen.getByRole('button', { name: /zoom into the regime timeline/i }),
  )
}

export async function clickZoomOut() {
  await userEvent.click(
    screen.getByRole('button', { name: /zoom out of the regime timeline/i }),
  )
}

export function zoomOutButton() {
  return screen.getByRole('button', {
    name: /zoom out of the regime timeline/i,
  })
}

export function zoomInButton() {
  return screen.getByRole('button', {
    name: /zoom into the regime timeline/i,
  })
}

export function expectLoadingSkeleton() {
  expect(
    document.querySelectorAll('[data-slot="skeleton"]').length,
  ).toBeGreaterThan(0)
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
}

export async function expectHistoryUnavailable() {
  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent(
      /regime history unavailable/i,
    )
  })
}

export async function expectNoRegimesClassified() {
  await waitFor(() => {
    expect(
      screen.getByText(/no regimes have been classified yet/i),
    ).toBeInTheDocument()
  })
}

/** Silence the expected console noise from a rejected query. */
export function silenceQueryErrors() {
  return vi.spyOn(console, 'error').mockImplementation(() => undefined)
}
