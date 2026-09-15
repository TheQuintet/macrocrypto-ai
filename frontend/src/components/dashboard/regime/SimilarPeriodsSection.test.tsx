import { cleanup, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchSimilarPeriods } from '@/api/regimes/similarPeriods'
import {
  NO_BTC_PERIOD,
  dialog,
  expectDetailsDialog,
  expectLoadingSkeleton,
  expectMatchMeter,
  expectNoComparablePeriod,
  expectNoDialog,
  expectPeriodCount,
  expectPeriodShown,
  expectPeriodsUnavailable,
  openPeriod,
  renderSimilarPeriods,
  silenceQueryErrors,
  similarPeriod,
  similarPeriods,
} from '@/components/dashboard/regime/SimilarPeriodsSection.testHelpers'

vi.mock('@/api/regimes/similarPeriods', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/api/regimes/similarPeriods')>()
  return { ...actual, fetchSimilarPeriods: vi.fn() }
})

const fetchPeriods = vi.mocked(fetchSimilarPeriods)

describe('SimilarPeriodsSection', () => {
  beforeEach(() => {
    fetchPeriods.mockReset()
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('shows the dates of each similar period', async () => {
    fetchPeriods.mockResolvedValue(similarPeriods([similarPeriod()]))
    renderSimilarPeriods()

    await expectPeriodShown('2018-06-01_2019-01-31', 'Jun 2018 – Jan 2019')
  })

  it('shows the reasoning behind each match', async () => {
    fetchPeriods.mockResolvedValue(similarPeriods([similarPeriod()]))
    renderSimilarPeriods()

    await expectPeriodShown(
      '2018-06-01_2019-01-31',
      'Policy rate near the top of its cycle',
    )
  })

  it('shows a confidence level for each suggestion', async () => {
    fetchPeriods.mockResolvedValue(similarPeriods([similarPeriod()]))
    renderSimilarPeriods()

    await expectPeriodShown('2018-06-01_2019-01-31', 'Match')
    expectMatchMeter('88%')
  })

  it('shows what BTC did through the period', async () => {
    fetchPeriods.mockResolvedValue(similarPeriods([similarPeriod()]))
    renderSimilarPeriods()

    await expectPeriodShown('2018-06-01_2019-01-31', 'BTC -50.7%')
  })

  it('says so rather than showing a zero when BTC did not trade then', async () => {
    fetchPeriods.mockResolvedValue(similarPeriods([NO_BTC_PERIOD]))
    renderSimilarPeriods()

    await expectPeriodShown('2006-03-01_2007-02-28', 'BTC —')
  })

  it('renders every match it was given', async () => {
    fetchPeriods.mockResolvedValue(
      similarPeriods([similarPeriod(), NO_BTC_PERIOD]),
    )
    renderSimilarPeriods()

    await expectPeriodShown('2018-06-01_2019-01-31', 'Jun 2018')
    expectPeriodCount(2)
  })

  it('opens the details of a period when it is clicked', async () => {
    fetchPeriods.mockResolvedValue(similarPeriods([similarPeriod()]))
    renderSimilarPeriods()

    await expectPeriodShown('2018-06-01_2019-01-31', 'Jun 2018')
    expectNoDialog()

    await openPeriod('2018-06-01_2019-01-31')

    await expectDetailsDialog('Jun 2018 – Jan 2019')
    expect(dialog()).toHaveTextContent('$7,480')
    expect(dialog()).toHaveTextContent('$3,690')
    expect(dialog()).toHaveTextContent('245')
  })

  it('compares the period conditions against today in the details', async () => {
    fetchPeriods.mockResolvedValue(similarPeriods([similarPeriod()]))
    renderSimilarPeriods()

    await expectPeriodShown('2018-06-01_2019-01-31', 'Jun 2018')
    await openPeriod('2018-06-01_2019-01-31')

    await expectDetailsDialog('Macro conditions, then vs now')
    // 2.90 then against 3.10 now — the comparison is the point of the panel.
    expect(dialog()).toHaveTextContent('2.90')
    expect(dialog()).toHaveTextContent('3.10')
  })

  it('says BTC history does not reach back when a period has none', async () => {
    fetchPeriods.mockResolvedValue(similarPeriods([NO_BTC_PERIOD]))
    renderSimilarPeriods()

    await expectPeriodShown('2006-03-01_2007-02-28', 'Mar 2006')
    await openPeriod('2006-03-01_2007-02-28')

    await expectDetailsDialog('did not trade far enough back')
  })

  it('labels simulated data so it cannot pass as real analysis', async () => {
    fetchPeriods.mockResolvedValue(
      similarPeriods([similarPeriod()], 'simulated'),
    )
    renderSimilarPeriods()

    await expectPeriodShown('2018-06-01_2019-01-31', 'Jun 2018')
    expect(screen.getByText('Simulated')).toBeInTheDocument()
  })

  it('shows no such label for live data', async () => {
    fetchPeriods.mockResolvedValue(similarPeriods([similarPeriod()]))
    renderSimilarPeriods()

    await expectPeriodShown('2018-06-01_2019-01-31', 'Jun 2018')
    expect(screen.queryByText('Simulated')).not.toBeInTheDocument()
  })

  it('shows a loading state while the matches are in flight', () => {
    fetchPeriods.mockReturnValue(new Promise(() => undefined))
    renderSimilarPeriods()

    expectLoadingSkeleton()
  })

  it('shows an error state when the request fails', async () => {
    silenceQueryErrors()
    fetchPeriods.mockRejectedValue(new Error('service unavailable'))
    renderSimilarPeriods()

    await expectPeriodsUnavailable()
  })

  it('reads no matches as nothing comparable, not as an error', async () => {
    fetchPeriods.mockResolvedValue(similarPeriods([]))
    renderSimilarPeriods()

    await expectNoComparablePeriod()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
