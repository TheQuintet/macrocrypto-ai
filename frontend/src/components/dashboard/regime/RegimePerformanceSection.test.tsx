import { cleanup, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchRegimePerformance } from '@/api/regimes/regimePerformance'
import {
  ACTIVE_ROW,
  expectCurrentBadgeOn,
  expectLoadingSkeleton,
  expectMetric,
  expectNoCurrentBadgeOn,
  expectNoRegimesMeasured,
  expectPerformanceUnavailable,
  expectRegimeOrder,
  expectRegimeRowShown,
  performance,
  performanceRow,
  renderRegimePerformance,
  silenceQueryErrors,
} from '@/components/dashboard/regime/RegimePerformanceSection.testHelpers'

vi.mock('@/api/regimes/regimePerformance', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/api/regimes/regimePerformance')>()
  return { ...actual, fetchRegimePerformance: vi.fn() }
})

const fetchPerformance = vi.mocked(fetchRegimePerformance)

describe('RegimePerformanceSection', () => {
  beforeEach(() => {
    fetchPerformance.mockReset()
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('names each regime in the table', async () => {
    fetchPerformance.mockResolvedValue(performance([performanceRow()]))
    renderRegimePerformance()

    await expectRegimeRowShown('growth', 'Growth')
  })

  it('shows every metric the ticket asks for', async () => {
    fetchPerformance.mockResolvedValue(performance([performanceRow()]))
    renderRegimePerformance()

    await expectRegimeRowShown('growth', 'Growth')
    expectMetric('growth', '+28.4%')
    expectMetric('growth', '-11.2%')
    expectMetric('growth', '+36.8%')
    expectMetric('growth', '1.42')
  })

  it('shows the period each regime covers', async () => {
    fetchPerformance.mockResolvedValue(performance([performanceRow()]))
    renderRegimePerformance()

    await expectRegimeRowShown('growth', 'Aug 2023 – Feb 2024')
  })

  it('marks the open regime as current and says its period runs to now', async () => {
    fetchPerformance.mockResolvedValue(
      performance([performanceRow(), ACTIVE_ROW]),
    )
    renderRegimePerformance()

    await expectRegimeRowShown('rising_rates', 'Mar 2024 – now')
    expectCurrentBadgeOn('rising_rates')
    expectNoCurrentBadgeOn('growth')
  })

  it('orders the table newest regime first, whatever order the API sent', async () => {
    // The endpoint appends the active regime after the completed ones, so
    // the newest row arrives last.
    fetchPerformance.mockResolvedValue(
      performance([performanceRow(), ACTIVE_ROW]),
    )
    renderRegimePerformance()

    await expectRegimeRowShown('rising_rates', 'Rising rates')
    expectRegimeOrder(['rising_rates', 'growth'])
  })

  it('shows a dash for a metric the service did not measure', async () => {
    fetchPerformance.mockResolvedValue(
      performance([
        performanceRow({
          performance: {
            ...performanceRow().performance,
            sharpeRatio: null,
          },
        }),
      ]),
    )
    renderRegimePerformance()

    await expectRegimeRowShown('growth', 'Growth')
    expectMetric('growth', '—')
  })

  it('labels simulated data so it cannot pass as measured returns', async () => {
    fetchPerformance.mockResolvedValue(
      performance([performanceRow()], 'simulated'),
    )
    renderRegimePerformance()

    await expectRegimeRowShown('growth', 'Growth')
    expect(screen.getByText('Simulated')).toBeInTheDocument()
  })

  it('shows no such label for live data', async () => {
    fetchPerformance.mockResolvedValue(performance([performanceRow()]))
    renderRegimePerformance()

    await expectRegimeRowShown('growth', 'Growth')
    expect(screen.queryByText('Simulated')).not.toBeInTheDocument()
  })

  it('shows a loading state while the metrics are in flight', () => {
    fetchPerformance.mockReturnValue(new Promise(() => undefined))
    renderRegimePerformance()

    expectLoadingSkeleton()
  })

  it('shows an error state when the request fails', async () => {
    silenceQueryErrors()
    fetchPerformance.mockRejectedValue(new Error('service unavailable'))
    renderRegimePerformance()

    await expectPerformanceUnavailable()
  })

  it('reads an empty history as nothing measured yet, not as an error', async () => {
    fetchPerformance.mockResolvedValue(performance([]))
    renderRegimePerformance()

    await expectNoRegimesMeasured()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
