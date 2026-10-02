import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  makePrediction,
  makePredictionHistory,
} from '@/api/predictions/btcPrediction.testHelpers'
import { makePredictionAccuracy } from '@/api/predictions/predictionAccuracy.testHelpers'
import { resetPredictionStore } from '@/stores/predictionStore.testHelpers'
import type { PredictionAccuracyParams } from '@/types/predictionAccuracy'
import type { PredictionParams } from '@/types/predictions'
import {
  expectAccuracyGrades,
  expectChartRendered,
  expectForecastUnavailable,
  expectLegendExplains,
  expectForecastMadeAt,
  expectNoSimulatedBadge,
  expectRangeCoverage,
  expectSimulatedBadge,
  expectSummaryValue,
  renderPanel,
} from './PredictionPanel.testHelpers'
import {
  expectConfidenceSelected,
  expectHorizonSelected,
  selectConfidence,
  selectHorizon,
} from './PredictionControls.testHelpers'

const { fetchBtcPrediction, fetchPredictionHistory, fetchPredictionAccuracy } =
  vi.hoisted(() => ({
    fetchBtcPrediction: vi.fn(),
    fetchPredictionHistory: vi.fn(),
    fetchPredictionAccuracy: vi.fn(),
  }))

vi.mock('@/api/predictions/btcPrediction', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/api/predictions/btcPrediction')>()
  return { ...actual, fetchBtcPrediction }
})

vi.mock('@/api/predictions/predictionHistory', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/api/predictions/predictionHistory')>()
  return { ...actual, fetchPredictionHistory }
})

vi.mock('@/api/predictions/predictionAccuracy', async (importOriginal) => {
  const actual =
    await importOriginal<typeof import('@/api/predictions/predictionAccuracy')>()
  return { ...actual, fetchPredictionAccuracy }
})

/** Echo the requested params back, so assertions can see what was asked for. */
function respondWithParams() {
  fetchBtcPrediction.mockImplementation(async (params: PredictionParams) =>
    makePrediction({
      horizon: params.horizon,
      confidence: params.confidence,
      predictedEndPrice: params.horizon === '7d' ? 66_000 : 64_200,
    }),
  )
}

describe('PredictionPanel', () => {
  beforeEach(() => {
    resetPredictionStore()
    fetchBtcPrediction.mockReset()
    fetchPredictionHistory.mockReset()
    fetchPredictionHistory.mockResolvedValue(makePredictionHistory())
    fetchPredictionAccuracy.mockReset()
    // Live, so the only "Simulated" badge on screen is the forecast's own.
    fetchPredictionAccuracy.mockImplementation(
      async (params: PredictionAccuracyParams) =>
        makePredictionAccuracy({ source: 'live', horizon: params.horizon }),
    )
    respondWithParams()
  })

  afterEach(() => {
    cleanup()
  })

  it('opens on the 24h forecast with its chart, legend and summary', async () => {
    renderPanel()

    await expectChartRendered('24h')
    expectHorizonSelected('24h')
    expectLegendExplains('85%')
    await expectRangeCoverage('85%')
  })

  it('says when the forecast was made', async () => {
    renderPanel()

    await expectChartRendered('24h')
    expectForecastMadeAt(makePrediction().predictionTime)
  })

  it('redraws the same chart for the 7d horizon', async () => {
    renderPanel()
    await expectChartRendered('24h')

    await selectHorizon('7d')

    await expectChartRendered('7d')
    expect(fetchBtcPrediction).toHaveBeenLastCalledWith({
      horizon: '7d',
      confidence: 0.85,
    })
  })

  it('updates the summary when the horizon changes', async () => {
    renderPanel()
    await expectSummaryValue('Current price', '$63,500.00')

    await selectHorizon('7d')

    await expectChartRendered('7d')
    expectHorizonSelected('7d')
  })

  it('refetches at the selected confidence and relabels the band', async () => {
    renderPanel()
    await expectChartRendered('24h')

    await selectConfidence('95%')

    expectConfidenceSelected('95%')
    expect(fetchBtcPrediction).toHaveBeenLastCalledWith({
      horizon: '24h',
      confidence: 0.95,
    })
    await expectRangeCoverage('95%')
    expectLegendExplains('95%')
  })

  it('labels a simulated batch so invented numbers are never read as live', async () => {
    renderPanel()

    await expectChartRendered('24h')
    expectSimulatedBadge()
  })

  it('shows no badge when the batch came from the service', async () => {
    fetchBtcPrediction.mockResolvedValue(makePrediction({ source: 'live' }))
    renderPanel()

    await expectChartRendered('24h')
    expectNoSimulatedBadge()
  })

  it('fetches more history than it shows, so zooming out has something to reveal', async () => {
    renderPanel()
    await expectChartRendered('24h')

    expect(fetchPredictionHistory).toHaveBeenLastCalledWith({
      horizon: '24h',
      range: '7d',
      interval: '1h',
    })
  })

  it('keeps the candles hourly for the 7d forecast, with a month to zoom through', async () => {
    renderPanel()
    await expectChartRendered('24h')

    await selectHorizon('7d')
    await expectChartRendered('7d')

    expect(fetchPredictionHistory).toHaveBeenLastCalledWith({
      horizon: '7d',
      range: '30d',
      interval: '1h',
    })
  })

  it('leaves the candles alone when only the confidence changes', async () => {
    renderPanel()
    await expectChartRendered('24h')
    const callsBefore = fetchPredictionHistory.mock.calls.length

    await selectConfidence('95%')
    await expectRangeCoverage('95%')

    expect(fetchPredictionHistory).toHaveBeenCalledTimes(callsBefore)
  })

  it('still draws the forecast when the candles fail to load', async () => {
    fetchPredictionHistory.mockRejectedValue(new Error('history down'))
    renderPanel()

    await expectChartRendered('24h')
    expectLegendExplains('85%')
  })

  it('grades past forecasts for the horizon on the chart', async () => {
    renderPanel()
    await expectChartRendered('24h')

    await selectHorizon('7d')
    await expectChartRendered('7d')

    await expectAccuracyGrades('7d')
    expect(fetchPredictionAccuracy).toHaveBeenCalledWith({
      horizon: '7d',
      days: 90,
    })
  })

  it('surfaces a failed request instead of falling back to fake forecasts', async () => {
    fetchBtcPrediction.mockRejectedValue(
      new Error('Prediction request failed with 404'),
    )
    renderPanel()

    await expectForecastUnavailable('Prediction request failed with 404')
  })
})
