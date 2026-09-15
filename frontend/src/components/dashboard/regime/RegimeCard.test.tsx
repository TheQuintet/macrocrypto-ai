import { cleanup, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchCurrentRegime } from '@/api/regimes/currentRegime'
import {
  expectConfidence,
  expectExplanationShown,
  expectIdentifiedAt,
  expectLoadingSkeleton,
  expectNotClassified,
  expectRegimeShown,
  expectRegimeUnavailable,
  expectStance,
  regimeWith,
  renderRegimeCard,
  silenceQueryErrors,
  REGIME,
} from '@/components/dashboard/regime/RegimeCard.testHelpers'

vi.mock('@/api/regimes/currentRegime', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/api/regimes/currentRegime')>()
  return { ...actual, fetchCurrentRegime: vi.fn() }
})

const fetchRegime = vi.mocked(fetchCurrentRegime)

describe('RegimeCard', () => {
  beforeEach(() => {
    fetchRegime.mockReset()
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('names the current regime once loaded', async () => {
    fetchRegime.mockResolvedValue(REGIME)
    renderRegimeCard()

    await expectRegimeShown('High inflation')
  })

  it('shows the bull / bear / recession indicator', async () => {
    fetchRegime.mockResolvedValue(REGIME)
    renderRegimeCard()

    await expectRegimeShown('High inflation')
    expectStance('Bear', 'bearish')
  })

  it('distinguishes a recession from an ordinary bear regime', async () => {
    fetchRegime.mockResolvedValue(
      regimeWith({ regimeType: 'recession', visualIndicator: 'recession' }),
    )
    renderRegimeCard()

    await expectRegimeShown('Recession')
    expectStance('Recession', 'bearish')
  })

  it('shows the confidence level as a figure and a bar', async () => {
    fetchRegime.mockResolvedValue(REGIME)
    renderRegimeCard()

    await expectRegimeShown('High inflation')
    expectConfidence('82%', '81.5%')
  })

  it('explains why the regime was identified', async () => {
    fetchRegime.mockResolvedValue(REGIME)
    renderRegimeCard()

    await expectRegimeShown('High inflation')
    expectExplanationShown(/CPI is running above/i)
  })

  it('prints when the classification was made', async () => {
    fetchRegime.mockResolvedValue(REGIME)
    renderRegimeCard()

    await expectRegimeShown('High inflation')
    expectIdentifiedAt('Jun 15, 01:00 UTC')
  })

  it('labels simulated data so it cannot pass as the real classification', async () => {
    fetchRegime.mockResolvedValue(regimeWith({ source: 'simulated' }))
    renderRegimeCard()

    await expectRegimeShown('High inflation')
    expect(screen.getByText('Simulated')).toBeInTheDocument()
  })

  it('shows no such label for live data', async () => {
    fetchRegime.mockResolvedValue(REGIME)
    renderRegimeCard()

    await expectRegimeShown('High inflation')
    expect(screen.queryByText('Simulated')).not.toBeInTheDocument()
  })

  it('shows a loading state while the classification is in flight', () => {
    fetchRegime.mockReturnValue(new Promise(() => undefined))
    renderRegimeCard()

    expectLoadingSkeleton()
  })

  it('shows an error state when the request fails', async () => {
    silenceQueryErrors()
    fetchRegime.mockRejectedValue(new Error('service unavailable'))
    renderRegimeCard()

    await expectRegimeUnavailable()
  })

  it('reads an unclassified backdrop as empty, not as an error', async () => {
    fetchRegime.mockResolvedValue(null)
    renderRegimeCard()

    await expectNotClassified()
    expect(screen.getByText(/not been classified yet/i)).toBeInTheDocument()
  })
})
