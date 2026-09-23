import { screen, waitFor } from '@testing-library/react'
import { expect, vi } from 'vitest'
import { RegimeCard } from '@/components/dashboard/regime/RegimeCard'
import { renderWithQuery } from '@/test/renderWithQuery'
import {
  CONFIDENCE_BAND_ORDER,
  formatConfidenceBand,
  formatConfidenceBandRange,
} from '@/lib/regimeDisplay'
import type {
  CurrentRegime,
  RegimeConfidenceBand,
  RegimeStance,
} from '@/types/regime'

export const REGIME: CurrentRegime = {
  source: 'live',
  id: 7,
  regimeType: 'high_inflation',
  confidence: 81.5,
  visualIndicator: 'bear',
  identifiedAt: '2024-06-15T01:00:00.000Z',
  expiresAt: '2024-06-16T01:00:00.000Z',
}

export function regimeWith(overrides: Partial<CurrentRegime>): CurrentRegime {
  return { ...REGIME, ...overrides }
}

export function renderRegimeCard() {
  return renderWithQuery(<RegimeCard />)
}

/** Scoped to the card title — `Recession` is also a stance label. */
export async function expectRegimeShown(label: string) {
  await waitFor(() => {
    expect(document.querySelector('[data-slot="card-title"]')).toHaveTextContent(
      label,
    )
  })
}

export function expectStance(stanceLabel: string, stance: RegimeStance) {
  const badge = document.querySelector('[data-stance]')

  expect(badge).toHaveTextContent(stanceLabel)
  expect(badge).toHaveAttribute('data-stance', stance)
}

export function expectIdentifiedAt(text: string) {
  expect(screen.getByText(`Identified ${text}`)).toBeInTheDocument()
}

export function expectConfidence(
  percent: string,
  width: string,
  band: RegimeConfidenceBand,
) {
  const meter = screen.getByRole('meter', {
    name: /regime classification confidence/i,
  })

  expect(
    screen.getByText(`${percent} ${formatConfidenceBand(band)}`),
  ).toBeInTheDocument()
  expect(meter).toHaveAttribute('data-confidence-band', band)
  expect(meter.firstElementChild).toHaveStyle({ width })
}

export function expectConfidenceScale() {
  for (const band of CONFIDENCE_BAND_ORDER) {
    expect(
      screen.getByText(
        `${formatConfidenceBand(band)} ${formatConfidenceBandRange(band)}`,
      ),
    ).toBeInTheDocument()
  }
}

export function expectExplanationShown(pattern: RegExp) {
  expect(screen.getByText(pattern)).toBeInTheDocument()
}

export function expectLoadingSkeleton() {
  expect(
    document.querySelectorAll('[data-slot="skeleton"]').length,
  ).toBeGreaterThan(0)
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
}

export async function expectRegimeUnavailable() {
  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent(/regime unavailable/i)
  })
}

export async function expectNotClassified() {
  await expectRegimeShown('Not classified')
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
}

/** Silence the expected console noise from a rejected query. */
export function silenceQueryErrors() {
  return vi.spyOn(console, 'error').mockImplementation(() => undefined)
}
