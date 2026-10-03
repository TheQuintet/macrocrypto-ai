import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  makePrediction,
  makePredictionHistory,
} from '@/api/predictions/btcPrediction.testHelpers'
import { routes } from '@/constants/navigation'
import {
  resetPredictionStore,
  setStoreConfidence,
  setStoreHorizon,
} from '@/stores/predictionStore.testHelpers'
import {
  expectCachedUnder,
  expectCandlesDrawn,
  expectFigure,
  expectForecastChart,
  expectForecastMadeAt,
  expectForecastPathAndBand,
  expectForecastsLink,
  expectForecastUnavailable,
  expectLegendNames,
  expectLegendOmits,
  expectLoading,
  expectNoCandlesDrawn,
  expectNoSimulatedBadge,
  expectRangeCoverage,
  expectSimulatedBadge,
  expectStoreHorizon,
  expectTrend,
  renderDashboardForecast,
} from './DashboardForecastCard.testHelpers'

const { fetchBtcPrediction, fetchPredictionHistory } = vi.hoisted(() => ({
  fetchBtcPrediction: vi.fn(),
  fetchPredictionHistory: vi.fn(),
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

describe('DashboardForecastCard', () => {
  beforeEach(() => {
    resetPredictionStore()
    fetchBtcPrediction.mockReset()
    fetchPredictionHistory.mockReset()
    fetchBtcPrediction.mockResolvedValue(makePrediction())
    fetchPredictionHistory.mockResolvedValue(makePredictionHistory())
  })

  afterEach(() => {
    cleanup()
  })

  it('draws the 24h forecast path and its band after the actual candles', async () => {
    renderDashboardForecast()

    await expectForecastChart('24h')
    expectForecastPathAndBand()
    expectCandlesDrawn()
    expectLegendNames(['Actual price', 'Forecast', '85% confidence band'])
  })

  it('shows the range coverage as the confidence value', async () => {
    renderDashboardForecast()
    await expectForecastChart()

    expectRangeCoverage('85%')
  })

  it('shows the predicted price, the expected change and the trend', async () => {
    renderDashboardForecast()
    await expectForecastChart()

    expectFigure('Predicted in 24 hours', '$64,200.00')
    expectFigure('Expected change', '+1.10%')
    expectTrend('up')
    expectFigure('Expected high', '$64,900.00')
    expectFigure('Expected low', '$63,400.00')
  })

  it('says when the forecast was made', async () => {
    renderDashboardForecast()
    await expectForecastChart()

    expectForecastMadeAt(makePrediction().predictionTime)
  })

  it('links through to the Forecasts page', async () => {
    renderDashboardForecast()
    await expectForecastChart()

    expectForecastsLink(routes.forecasts)
  })

  it('labels a simulated batch', async () => {
    renderDashboardForecast()
    await expectForecastChart()

    expectSimulatedBadge()
  })

  it('shows no badge for a live batch', async () => {
    fetchBtcPrediction.mockResolvedValue(makePrediction({ source: 'live' }))
    renderDashboardForecast()
    await expectForecastChart()

    expectNoSimulatedBadge()
  })

  it('holds a skeleton in place while the forecast loads', () => {
    fetchBtcPrediction.mockReturnValue(new Promise(() => {}))
    renderDashboardForecast()

    expectLoading()
    expectForecastsLink(routes.forecasts)
  })

  it('says the forecast is unavailable when the request fails', async () => {
    fetchBtcPrediction.mockRejectedValue(
      new Error('Prediction request failed with 503'),
    )
    renderDashboardForecast()

    await expectForecastUnavailable('Prediction request failed with 503')
  })

  it('still draws the forecast when the candles fail to load', async () => {
    fetchPredictionHistory.mockRejectedValue(new Error('history down'))
    renderDashboardForecast()

    await expectForecastChart()
    expectForecastPathAndBand()
    expectNoCandlesDrawn()
    expectLegendOmits('Actual price')
  })

  it('stays on 24h at 85% whatever the Forecasts page has selected', async () => {
    setStoreHorizon('7d')
    setStoreConfidence(0.95)
    renderDashboardForecast()

    await expectForecastChart('24h')
    expect(fetchBtcPrediction).toHaveBeenCalledTimes(1)
    expect(fetchBtcPrediction).toHaveBeenCalledWith({
      horizon: '24h',
      confidence: 0.85,
    })
    expect(fetchPredictionHistory).toHaveBeenCalledWith({
      horizon: '24h',
      range: '7d',
      interval: '1h',
    })
    expectStoreHorizon('7d')
  })

  it("shares the Forecasts page's 24h cache entry", async () => {
    const client = renderDashboardForecast()
    await expectForecastChart()

    expectCachedUnder(client, { horizon: '24h', confidence: 0.85 })
  })
})
