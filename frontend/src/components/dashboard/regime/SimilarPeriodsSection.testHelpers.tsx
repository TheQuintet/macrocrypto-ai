import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, vi } from 'vitest'
import { SimilarPeriodsSection } from '@/components/dashboard/regime/SimilarPeriodsSection'
import { renderWithQuery } from '@/test/renderWithQuery'
import type { SimilarPeriod, SimilarPeriods } from '@/types/regime'

export function similarPeriod(
  overrides: Partial<SimilarPeriod> = {},
): SimilarPeriod {
  return {
    id: '2018-06-01_2019-01-31',
    periodStart: '2018-06-01',
    periodEnd: '2019-01-31',
    distance: 0.18,
    similarityScore: 88.4,
    reason: 'Policy rate near the top of its cycle, with inflation easing.',
    matchingIndicators: [
      { indicator: 'federal_funds_rate', normalizedDifference: 0.06 },
    ],
    macroConditions: { cpi: 2.9, federal_funds_rate: 5.0 },
    btcPerformance: {
      priceStart: 7_480,
      priceEnd: 3_690,
      returnPercent: -50.7,
      observations: 245,
    },
    ...overrides,
  }
}

export const NO_BTC_PERIOD = similarPeriod({
  id: '2006-03-01_2007-02-28',
  periodStart: '2006-03-01',
  periodEnd: '2007-02-28',
  similarityScore: 81.2,
  reason: 'Rates held high after a tightening cycle.',
  btcPerformance: null,
})

export function similarPeriods(
  periods: SimilarPeriod[],
  source: SimilarPeriods['source'] = 'live',
): SimilarPeriods {
  return {
    source,
    method: 'normalized Euclidean distance',
    currentConditions: { cpi: 3.1, federal_funds_rate: 5.25 },
    periods,
    message: null,
  }
}

export function renderSimilarPeriods() {
  return renderWithQuery(<SimilarPeriodsSection />)
}

function periodCard(periodId: string) {
  const card = document.querySelector(
    '[data-similar-period="' + periodId + '"]',
  )

  expect(card).not.toBeNull()
  return card as HTMLElement
}

export async function expectPeriodShown(periodId: string, text: string) {
  await waitFor(() => {
    expect(periodCard(periodId)).toHaveTextContent(text)
  })
}

export function expectPeriodCount(count: number) {
  expect(document.querySelectorAll('[data-similar-period]')).toHaveLength(count)
}

export function expectMatchMeter(score: string) {
  const meters = screen.getAllByRole('meter', {
    name: /similarity to the current environment/i,
  })

  expect(meters.length).toBeGreaterThan(0)
  expect(screen.getAllByText(score).length).toBeGreaterThan(0)
}

export async function openPeriod(periodId: string) {
  await userEvent.click(periodCard(periodId))
}

export async function expectDetailsDialog(text: string) {
  await waitFor(() => {
    expect(screen.getByRole('dialog')).toHaveTextContent(text)
  })
}

export function dialog() {
  return screen.getByRole('dialog')
}

export function expectNoDialog() {
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
}

export function expectLoadingSkeleton() {
  expect(
    document.querySelectorAll('[data-slot="skeleton"]').length,
  ).toBeGreaterThan(0)
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
}

export async function expectPeriodsUnavailable() {
  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent(
      /similar periods unavailable/i,
    )
  })
}

export async function expectNoComparablePeriod() {
  await waitFor(() => {
    expect(
      screen.getByText(/no comparable period was found/i),
    ).toBeInTheDocument()
  })
}

/** Silence the expected console noise from a rejected query. */
export function silenceQueryErrors() {
  return vi.spyOn(console, 'error').mockImplementation(() => undefined)
}
