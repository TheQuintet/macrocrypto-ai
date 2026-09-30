import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  makeAccuracyThreshold,
  makeMapeWarning,
  makePredictionAccuracy,
} from '@/api/predictions/predictionAccuracy.testHelpers'
import {
  resetPredictionStore,
  setStoreHorizon,
} from '@/stores/predictionStore.testHelpers'
import type { PredictionAccuracyParams } from '@/types/predictionAccuracy'
import {
  closeDetails,
  expectAccuracyStat,
  expectBreakdownRow,
  expectCheckStatus,
  expectDescription,
  expectDetailsClosed,
  expectMetricTone,
  expectNoSimulatedBadge,
  expectNoWarning,
  expectNothingScoredYet,
  expectScore,
  expectScoreTone,
  expectSimulatedBadge,
  expectStatTone,
  expectStatUntoned,
  expectTrendChart,
  expectUnavailable,
  expectWarning,
  openDetails,
  renderAccuracyCard,
} from './PredictionAccuracyCard.testHelpers'

const { fetchPredictionAccuracy } = vi.hoisted(() => ({
  fetchPredictionAccuracy: vi.fn(),
}))

vi.mock('@/api/predictions/predictionAccuracy', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/api/predictions/predictionAccuracy')>()
  return { ...actual, fetchPredictionAccuracy }
})

describe('PredictionAccuracyCard', () => {
  beforeEach(() => {
    resetPredictionStore()
    fetchPredictionAccuracy.mockReset()
    fetchPredictionAccuracy.mockImplementation(
      async (params: PredictionAccuracyParams) =>
        makePredictionAccuracy({ horizon: params.horizon }),
    )
  })

  afterEach(() => {
    cleanup()
  })

  it('leads with price accuracy, as the service scores it today', async () => {
    renderAccuracyCard()

    await expectScore('98%', 'price accuracy (100% minus the average % miss)')
  })

  it('leads with direction instead once the service reports it', async () => {
    fetchPredictionAccuracy.mockResolvedValue(
      makePredictionAccuracy({
        metrics: {
          mae: 1_152,
          rmse: 1_555,
          mape: 1.8,
          directionalAccuracy: 61.5,
        },
      }),
    )
    renderAccuracyCard()

    await expectScore('62%', 'of forecasts called the direction right')
  })

  it('reports the figures behind the score in plain language', async () => {
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    expectAccuracyStat('Typical miss', '$1,152')
    expectAccuracyStat('Average % miss', '1.80%')
    expectAccuracyStat('Forecasts checked', '720')
    expectAccuracyStat('Period', 'Last 30 days')
    // ICU spells the en-GB short month `Sep` or `Sept` depending on version.
    expectAccuracyStat('Last scored', /^14 Sept? 2026$/)
  })

  it('names the model and the horizon it is grading', async () => {
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    expectDescription(
      'Prophet (fresh) · best model, past 24h forecasts checked against the real price',
    )
  })

  it('draws the accuracy trend', async () => {
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    expectTrendChart()
  })

  it("repeats the service's warning in words", async () => {
    fetchPredictionAccuracy.mockResolvedValue(
      makePredictionAccuracy({
        warning: true,
        warningCount: 1,
        thresholds: [makeMapeWarning()],
      }),
    )
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    expectWarning('Average % miss has been above 10% for 4 days in a row.')
  })

  it('warns even when the flagged metric is missing from the checks', async () => {
    fetchPredictionAccuracy.mockResolvedValue(
      makePredictionAccuracy({ warning: true, warningCount: 1 }),
    )
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    expectWarning(
      'The service has flagged 1 metric outside its bound for 3+ days in a row.',
    )
  })

  it('stays quiet while every check is inside its bounds', async () => {
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    expectNoWarning()
  })

  it('greens the figures the service grades as inside their bounds', async () => {
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    expectScoreTone('98%', 'text-positive')
    expectStatTone('Typical miss', '$1,152', 'text-positive')
    expectStatTone('Average % miss', '1.80%', 'text-positive')
  })

  it('ambers the headline while the service warns about it', async () => {
    fetchPredictionAccuracy.mockResolvedValue(
      makePredictionAccuracy({
        warning: true,
        warningCount: 1,
        metrics: {
          mae: 6_912,
          rmse: 9_331,
          mape: 10.8,
          directionalAccuracy: null,
        },
        thresholds: [makeMapeWarning()],
      }),
    )
    renderAccuracyCard()
    await expectScore('89%', /price accuracy/)

    expectScoreTone('89%', 'text-warning')
  })

  it('leaves figures without a bound uncoloured', async () => {
    fetchPredictionAccuracy.mockResolvedValue(
      makePredictionAccuracy({
        // No `mae_pct` check — the service drops it without a mean price.
        thresholds: [
          makeAccuracyThreshold({
            metric: 'mape',
            value: 1.8,
            threshold: 10,
            breachDirection: 'above',
          }),
        ],
      }),
    )
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    expectStatUntoned('Typical miss', '$1,152')
    expectStatUntoned('Forecasts checked', '720')
  })

  it('grades whichever horizon the chart is showing', async () => {
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    setStoreHorizon('7d')

    await vi.waitFor(() => {
      expect(fetchPredictionAccuracy).toHaveBeenLastCalledWith({
        horizon: '7d',
        days: 30,
      })
    })
    await vi.waitFor(() => {
      expectDescription(/past 7d forecasts/)
    })
  })

  it('labels simulated scores so they are never read as live', async () => {
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    expectSimulatedBadge()
  })

  it('shows no badge on scores from the service', async () => {
    fetchPredictionAccuracy.mockResolvedValue(
      makePredictionAccuracy({ source: 'live' }),
    )
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    expectNoSimulatedBadge()
  })

  it('opens the full scorecard with the market breakdown and checks', async () => {
    fetchPredictionAccuracy.mockResolvedValue(
      makePredictionAccuracy({
        warning: true,
        warningCount: 1,
        thresholds: [makeMapeWarning()],
      }),
    )
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)

    const dialog = await openDetails()

    expectBreakdownRow(dialog, 'Bull market', ['$980', '1.53%', '252'])
    expectBreakdownRow(dialog, 'Volatile', ['$1,843', '2.88%', '108'])
    expectCheckStatus(dialog, 'Average % miss', 'Warning')
  })

  it('closes the scorecard from its Close button', async () => {
    renderAccuracyCard()
    await expectScore('98%', /price accuracy/)
    const dialog = await openDetails()

    await closeDetails(dialog)

    expectDetailsClosed()
  })

  it('colours each graded figure by its check', async () => {
    fetchPredictionAccuracy.mockResolvedValue(
      makePredictionAccuracy({
        warning: true,
        warningCount: 1,
        metrics: {
          mae: 1_152,
          rmse: 1_555,
          mape: 10.8,
          directionalAccuracy: null,
        },
        thresholds: [
          makeAccuracyThreshold({
            metric: 'mae_pct',
            value: 1.8,
            threshold: 10,
            breachDirection: 'above',
          }),
          makeMapeWarning(),
        ],
      }),
    )
    renderAccuracyCard()
    await expectScore('89%', /price accuracy/)

    const dialog = await openDetails()

    expectMetricTone(dialog, '$1,152', 'text-positive')
    expectMetricTone(dialog, '10.80%', 'text-warning')
  })

  it('surfaces a failed request instead of inventing a score', async () => {
    fetchPredictionAccuracy.mockRejectedValue(
      new Error('Accuracy request failed with 404'),
    )
    renderAccuracyCard()

    await expectUnavailable('Accuracy request failed with 404')
  })

  it('says so when nothing has been scored for the horizon yet', async () => {
    fetchPredictionAccuracy.mockResolvedValue(null)
    renderAccuracyCard()

    await expectNothingScoredYet()
  })
})
