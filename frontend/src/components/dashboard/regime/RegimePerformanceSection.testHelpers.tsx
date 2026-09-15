import { screen, waitFor, within } from '@testing-library/react'
import { expect, vi } from 'vitest'
import { RegimePerformanceSection } from '@/components/dashboard/regime/RegimePerformanceSection'
import { renderWithQuery } from '@/test/renderWithQuery'
import type { RegimePerformance, RegimePerformanceRow } from '@/types/regime'

export function performanceRow(
  overrides: Partial<RegimePerformanceRow> = {},
): RegimePerformanceRow {
  return {
    regimeId: 4,
    regimeType: 'growth',
    startDate: '2023-08-01',
    endDate: '2024-02-29',
    status: 'completed',
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

export const ACTIVE_ROW = performanceRow({
  regimeId: 5,
  regimeType: 'rising_rates',
  startDate: '2024-03-01',
  endDate: null,
  status: 'active',
  performance: {
    avgReturn: -4.2,
    maxDrawdown: -18.6,
    volatility: 41.3,
    sharpeRatio: -0.21,
    btcPriceStart: 61_400,
    btcPriceEnd: 58_820,
  },
})

export function performance(
  rows: RegimePerformanceRow[],
  source: RegimePerformance['source'] = 'live',
): RegimePerformance {
  return { source, rows }
}

export function renderRegimePerformance() {
  return renderWithQuery(<RegimePerformanceSection />)
}

function regimeRow(regimeType: string) {
  const row = document.querySelector('[data-regime="' + regimeType + '"]')

  expect(row).not.toBeNull()
  return row as HTMLElement
}

export async function expectRegimeRowShown(regimeType: string, label: string) {
  await waitFor(() => {
    expect(regimeRow(regimeType)).toHaveTextContent(label)
  })
}

export function expectMetric(regimeType: string, text: string) {
  expect(regimeRow(regimeType)).toHaveTextContent(text)
}

export function expectCurrentBadgeOn(regimeType: string) {
  expect(within(regimeRow(regimeType)).getByText('Current')).toBeInTheDocument()
}

export function expectNoCurrentBadgeOn(regimeType: string) {
  expect(within(regimeRow(regimeType)).queryByText('Current')).toBeNull()
}

/** Table order top-to-bottom, newest regime first. */
export function expectRegimeOrder(regimeTypes: string[]) {
  const rendered = Array.from(document.querySelectorAll('[data-regime]')).map(
    (row) => row.getAttribute('data-regime'),
  )

  expect(rendered).toEqual(regimeTypes)
}

export function expectLoadingSkeleton() {
  expect(
    document.querySelectorAll('[data-slot="skeleton"]').length,
  ).toBeGreaterThan(0)
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
}

export async function expectPerformanceUnavailable() {
  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent(
      /regime performance unavailable/i,
    )
  })
}

export async function expectNoRegimesMeasured() {
  await waitFor(() => {
    expect(
      screen.getByText(/no regimes have been measured yet/i),
    ).toBeInTheDocument()
  })
}

/** Silence the expected console noise from a rejected query. */
export function silenceQueryErrors() {
  return vi.spyOn(console, 'error').mockImplementation(() => undefined)
}
