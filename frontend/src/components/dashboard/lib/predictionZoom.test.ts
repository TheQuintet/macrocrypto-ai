import { describe, expect, it } from 'vitest'
import {
  clampPredictionZoom,
  isFullyZoomedOut,
  PREDICTION_ZOOM_MAX,
  PREDICTION_ZOOM_MIN,
  visibleHistoryCount,
  visiblePredictionRows,
  zoomPredictionStep,
} from '@/components/dashboard/lib/predictionZoom'
import type { PredictionChartRow, PredictionRowKind } from '@/types/predictions'

const HOUR = 60 * 60 * 1000

function makeRows(kinds: PredictionRowKind[]): PredictionChartRow[] {
  return kinds.map((kind, index) => ({
    kind,
    time: new Date(index * HOUR).toISOString(),
    timeMs: index * HOUR,
  }))
}

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
    expect(visibleHistoryCount(0, 24, 168)).toBe(24)
    expect(visibleHistoryCount(0, 168, 720)).toBe(168)
  })

  it('reaches every fetched candle at the last step, for either horizon', () => {
    expect(visibleHistoryCount(PREDICTION_ZOOM_MAX, 24, 168)).toBe(168)
    expect(visibleHistoryCount(PREDICTION_ZOOM_MAX, 168, 720)).toBe(720)
  })

  it('widens each step by roughly the same ratio', () => {
    const counts = [0, 1, 2, 3, 4].map((zoom) =>
      visibleHistoryCount(zoom, 168, 720),
    )
    const ratios = counts.slice(1).map((count, index) => count / counts[index])

    for (const ratio of ratios) {
      expect(ratio).toBeCloseTo(ratios[0], 1)
    }
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

describe('visiblePredictionRows', () => {
  it('keeps as much history as forecast at rest', () => {
    const rows = makeRows([
      ...Array<PredictionRowKind>(10).fill('history'),
      ...Array<PredictionRowKind>(3).fill('forecast'),
    ])

    const shown = visiblePredictionRows(rows, 0)

    expect(shown.filter((row) => row.kind === 'history')).toHaveLength(3)
    expect(shown.filter((row) => row.kind === 'forecast')).toHaveLength(3)
  })

  it('shows the whole fetched history at the widest step', () => {
    const rows = makeRows([
      ...Array<PredictionRowKind>(10).fill('history'),
      ...Array<PredictionRowKind>(3).fill('forecast'),
    ])

    expect(visiblePredictionRows(rows, PREDICTION_ZOOM_MAX)).toHaveLength(13)
  })

  /**
   * An old batch can have candles past its forecast start. They belong to
   * the always-visible side of the window and must stay in time order.
   */
  it('keeps candles past the forecast start, in time order', () => {
    const rows = makeRows([
      'history',
      'history',
      'history',
      'forecast',
      'forecast',
      'history',
    ])

    const shown = visiblePredictionRows(rows, 0)

    expect(shown.map((row) => row.timeMs)).toEqual(
      [...shown].sort((a, b) => a.timeMs - b.timeMs).map((row) => row.timeMs),
    )
    expect(shown[shown.length - 1]).toBe(rows[rows.length - 1])
  })

  it('leaves a history-only set untouched', () => {
    const rows = makeRows(['history', 'history'])

    expect(visiblePredictionRows(rows, 0)).toEqual(rows)
  })
})
