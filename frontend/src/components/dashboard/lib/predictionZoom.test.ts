import { describe, expect, it } from 'vitest'
import {
  clampPredictionZoom,
  isFullyZoomedOut,
  PREDICTION_ZOOM_MAX,
  PREDICTION_ZOOM_MIN,
  visibleHistoryCount,
  zoomPredictionStep,
} from '@/components/dashboard/lib/predictionZoom'

describe('zoomPredictionStep', () => {
  it('widens the window on the way out and narrows it on the way in', () => {
    expect(zoomPredictionStep(1, 'out')).toBe(2)
    expect(zoomPredictionStep(1, 'in')).toBe(0)
  })

  it('stops at the resting window rather than going past it', () => {
    expect(zoomPredictionStep(PREDICTION_ZOOM_MIN, 'in')).toBe(
      PREDICTION_ZOOM_MIN,
    )
  })

  it('stops at the widest step', () => {
    expect(zoomPredictionStep(PREDICTION_ZOOM_MAX, 'out')).toBe(
      PREDICTION_ZOOM_MAX,
    )
  })
})

describe('clampPredictionZoom', () => {
  it('holds a stored value inside the range the buttons can reach', () => {
    expect(clampPredictionZoom(-5)).toBe(PREDICTION_ZOOM_MIN)
    expect(clampPredictionZoom(99)).toBe(PREDICTION_ZOOM_MAX)
  })
})

describe('visibleHistoryCount', () => {
  it('shows as much history as forecast at rest, so the label stays true', () => {
    expect(visibleHistoryCount(0, 7, 30)).toBe(7)
    expect(visibleHistoryCount(0, 24, 168)).toBe(24)
  })

  it('widens with each step out', () => {
    const counts = [0, 1, 2, 3].map((zoom) => visibleHistoryCount(zoom, 24, 168))

    expect(counts).toEqual([...counts].sort((a, b) => a - b))
    expect(counts[3]).toBeGreaterThan(counts[0])
  })

  it('never shows more than was fetched', () => {
    expect(visibleHistoryCount(PREDICTION_ZOOM_MAX, 7, 30)).toBe(30)
  })

  it('never falls below the forecast, so the halves stay comparable', () => {
    expect(visibleHistoryCount(0, 24, 500)).toBe(24)
  })

  it('degrades to what exists when little history came back', () => {
    expect(visibleHistoryCount(2, 24, 5)).toBe(5)
  })
})

describe('isFullyZoomedOut', () => {
  it('reports the point past which zooming out reveals nothing', () => {
    expect(isFullyZoomedOut(PREDICTION_ZOOM_MAX, 7, 30)).toBe(true)
    expect(isFullyZoomedOut(0, 7, 30)).toBe(false)
  })

  it('is immediately true when history is no longer than the forecast', () => {
    expect(isFullyZoomedOut(0, 24, 24)).toBe(true)
  })
})
