import { cleanup, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchRegimeHistory } from '@/api/regimes/regimeHistory'
import {
  CURRENT_ROW,
  clickSegment,
  clickZoomIn,
  clickZoomOut,
  expectCurrentHighlight,
  expectDetailsDialog,
  expectHistoryUnavailable,
  expectLoadingSkeleton,
  expectNoCurrentHighlight,
  expectNoDetailsDialog,
  expectNoRegimesClassified,
  expectSegmentCount,
  expectSegmentShown,
  expectSegmentWiderThan,
  expectYearTick,
  history,
  historyRow,
  renderRegimeTimeline,
  silenceQueryErrors,
  zoomInButton,
  zoomLevel,
  zoomOutButton,
} from '@/components/dashboard/regime/RegimeTimelineSection.testHelpers'

vi.mock('@/api/regimes/regimeHistory', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/api/regimes/regimeHistory')>()
  return { ...actual, fetchRegimeHistory: vi.fn() }
})

const fetchHistory = vi.mocked(fetchRegimeHistory)

describe('RegimeTimelineSection', () => {
  beforeEach(() => {
    fetchHistory.mockReset()
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('draws one segment per classified regime', async () => {
    fetchHistory.mockResolvedValue(history([historyRow(), CURRENT_ROW]))
    renderRegimeTimeline()

    await expectSegmentShown('growth')
    expectSegmentCount(2)
  })

  it('sizes a segment by how long its regime ran', async () => {
    fetchHistory.mockResolvedValue(
      history([
        historyRow({ id: 1, regimeType: 'recession', startDate: '2022-01-01', endDate: '2023-01-01' }),
        historyRow({ id: 2, regimeType: 'growth', startDate: '2023-01-01', endDate: '2023-03-01' }),
      ]),
    )
    renderRegimeTimeline()

    await expectSegmentShown('recession')
    expectSegmentWiderThan('recession', 'growth')
  })

  it('highlights the regime we are currently in', async () => {
    fetchHistory.mockResolvedValue(history([historyRow(), CURRENT_ROW]))
    renderRegimeTimeline()

    await expectSegmentShown('rising_rates')
    expectCurrentHighlight('rising_rates')
    expectNoCurrentHighlight('growth')
  })

  it('marks the year boundaries the span crosses', async () => {
    fetchHistory.mockResolvedValue(
      history([
        historyRow({ startDate: '2022-06-01', endDate: '2024-03-01' }),
      ]),
    )
    renderRegimeTimeline()

    await expectSegmentShown('growth')
    expectYearTick('2023')
    expectYearTick('2024')
  })

  it('opens the details for a regime when it is clicked', async () => {
    fetchHistory.mockResolvedValue(history([historyRow()]))
    renderRegimeTimeline()

    await expectSegmentShown('growth')
    expectNoDetailsDialog()

    await clickSegment('growth')

    await expectDetailsDialog('Growth')
    expect(screen.getByRole('dialog')).toHaveTextContent('+28.4%')
  })

  it('says performance is pending for the regime still running', async () => {
    fetchHistory.mockResolvedValue(history([CURRENT_ROW]))
    renderRegimeTimeline()

    await expectSegmentShown('rising_rates')
    await clickSegment('rising_rates')

    await expectDetailsDialog('Rising rates')
    expect(screen.getByRole('dialog')).toHaveTextContent(
      /measured once the regime closes/i,
    )
  })

  it('zooms in and back out, stopping at each end of the range', async () => {
    fetchHistory.mockResolvedValue(history([historyRow(), CURRENT_ROW]))
    renderRegimeTimeline()

    await expectSegmentShown('growth')
    expect(zoomLevel()).toBe('1x')
    expect(zoomOutButton()).toBeDisabled()

    await clickZoomIn()
    expect(zoomLevel()).toBe('2x')
    expect(zoomOutButton()).toBeEnabled()

    await clickZoomIn()
    await clickZoomIn()
    expect(zoomLevel()).toBe('8x')
    expect(zoomInButton()).toBeDisabled()

    await clickZoomOut()
    expect(zoomLevel()).toBe('4x')
  })

  it('labels simulated data so it cannot pass as the real history', async () => {
    fetchHistory.mockResolvedValue(history([historyRow()], 'simulated'))
    renderRegimeTimeline()

    await expectSegmentShown('growth')
    expect(screen.getByText('Simulated')).toBeInTheDocument()
  })

  it('shows no such label for live data', async () => {
    fetchHistory.mockResolvedValue(history([historyRow()]))
    renderRegimeTimeline()

    await expectSegmentShown('growth')
    expect(screen.queryByText('Simulated')).not.toBeInTheDocument()
  })

  it('shows a loading state while the history is in flight', () => {
    fetchHistory.mockReturnValue(new Promise(() => undefined))
    renderRegimeTimeline()

    expectLoadingSkeleton()
  })

  it('shows an error state when the request fails', async () => {
    silenceQueryErrors()
    fetchHistory.mockRejectedValue(new Error('service unavailable'))
    renderRegimeTimeline()

    await expectHistoryUnavailable()
  })

  it('reads an empty history as nothing classified yet, not as an error', async () => {
    fetchHistory.mockResolvedValue(history([]))
    renderRegimeTimeline()

    await expectNoRegimesClassified()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
