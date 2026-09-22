import { describe, expect, it } from 'vitest'
import {
  changeFromCurrentPercent,
  fitPoints,
  forecastPoints,
  inferStepMs,
  forecastStartMs,
  formatConfidencePercent,
  formatPredictionTick,
  MEDIUM_BAND_MAX_PERCENT,
  NARROW_BAND_MAX_PERCENT,
  predictionBandWidth,
  predictionBandWidthPercent,
  predictionChartRows,
  predictionKeyLevels,
  predictionYDomain,
  usesCompactTicks,
} from '@/components/dashboard/lib/predictionChart'
import type { ChartCandle } from '@/types/chart'
import type { BtcPrediction, PredictionPoint } from '@/types/predictions'

function makePoint(overrides: Partial<PredictionPoint> = {}): PredictionPoint {
  const timeMs = overrides.timeMs ?? Date.UTC(2024, 5, 15, 13)

  return {
    time: new Date(timeMs).toISOString(),
    timeMs,
    predictedPrice: 64_000,
    lowerBound: 63_500,
    upperBound: 64_500,
    ...overrides,
  }
}

const POINTS: PredictionPoint[] = [
  makePoint({ timeMs: Date.UTC(2024, 5, 15, 13), lowerBound: 63_800, upperBound: 64_200 }),
  makePoint({ timeMs: Date.UTC(2024, 5, 15, 14), lowerBound: 63_400, upperBound: 64_900 }),
  makePoint({ timeMs: Date.UTC(2024, 5, 15, 15), lowerBound: 63_600, upperBound: 64_600 }),
]

function makeCandle(overrides: Partial<ChartCandle> = {}): ChartCandle {
  const timeMs = overrides.timeMs ?? Date.UTC(2024, 5, 15, 11)

  return {
    time: new Date(timeMs).toISOString(),
    timeMs,
    open: 63_000,
    high: 63_400,
    low: 62_900,
    close: 63_200,
    ...overrides,
  }
}

const CANDLES: ChartCandle[] = [
  makeCandle({ timeMs: Date.UTC(2024, 5, 15, 11) }),
  makeCandle({ timeMs: Date.UTC(2024, 5, 15, 12), close: 63_600 }),
]

describe('formatConfidencePercent', () => {
  it('reads the wire float as a percentage', () => {
    expect(formatConfidencePercent(0.7)).toBe('70%')
    expect(formatConfidencePercent(0.85)).toBe('85%')
    expect(formatConfidencePercent(0.95)).toBe('95%')
  })
})

describe('formatPredictionTick', () => {
  it('ticks hourly points by clock time', () => {
    expect(formatPredictionTick(Date.UTC(2024, 5, 15, 13, 30), '24h')).toMatch(
      /^\d{2}:\d{2}$/,
    )
  })

  it('ticks daily points by date', () => {
    expect(formatPredictionTick(Date.UTC(2024, 5, 15), '7d')).toMatch(
      /^\d{2} \w{3}$/,
    )
  })
})

const BOUNDARY_MS = Date.UTC(2024, 5, 15, 12, 30)

/** A batch whose points straddle `prediction_time`, as a fitted one does. */
function makeBatch(points: PredictionPoint[] = POINTS): BtcPrediction {
  return {
    source: 'simulated',
    horizon: '24h',
    modelName: 'prophet',
    confidence: 0.85,
    predictionTime: new Date(BOUNDARY_MS).toISOString(),
    currentPrice: 64_000,
    predictedEndPrice: 64_000,
    priceChangePct: 0,
    trend: 'neutral',
    points,
  }
}

const FIT_POINT = makePoint({
  timeMs: Date.UTC(2024, 5, 15, 12),
  predictedPrice: 63_600,
  lowerBound: 63_500,
  upperBound: 63_700,
})

describe('fitPoints / forecastPoints', () => {
  it('splits the batch at the moment it was generated', () => {
    const batch = makeBatch([FIT_POINT, ...POINTS])

    expect(fitPoints(batch)).toEqual([FIT_POINT])
    expect(forecastPoints(batch)).toEqual(POINTS)
  })

  it("reads today's forward-only batch as all forecast, no fit", () => {
    const batch = makeBatch()

    expect(fitPoints(batch)).toEqual([])
    expect(forecastPoints(batch)).toHaveLength(POINTS.length)
  })
})

describe('predictionChartRows', () => {
  it('pairs the bounds into the band the area plots', () => {
    const row = predictionChartRows(makeBatch())[0]

    expect(row.band).toEqual([row.lower, row.upper])
    expect(row.lower).toBe(63_800)
    expect(row.upper).toBe(64_200)
  })

  it('keeps one row per forecast point, in order', () => {
    const rows = predictionChartRows(makeBatch())

    expect(rows).toHaveLength(POINTS.length)
    expect(rows.map((row) => row.timeMs)).toEqual(
      POINTS.map((point) => point.timeMs),
    )
  })

  it('merges a candle and the model value for the same moment into one row', () => {
    const candle = makeCandle({ timeMs: FIT_POINT.timeMs })
    const rows = predictionChartRows(makeBatch([FIT_POINT, ...POINTS]), [candle])
    const merged = rows.find((row) => row.timeMs === FIT_POINT.timeMs)!

    expect(merged.kind).toBe('history')
    expect(merged.candle).toEqual([candle.low, candle.high])
    expect(merged.fit).toBe(FIT_POINT.predictedPrice)
  })

  it('puts the model value on `fit` behind now and `predicted` ahead of it', () => {
    const earlier = makePoint({
      timeMs: Date.UTC(2024, 5, 15, 11),
      predictedPrice: 63_300,
    })
    const rows = predictionChartRows(
      makeBatch([earlier, FIT_POINT, ...POINTS]),
    )
    const past = rows.find((row) => row.timeMs === earlier.timeMs)!
    const ahead = rows.find((row) => row.timeMs === POINTS[1].timeMs)!

    expect(past.fit).toBe(63_300)
    expect(past.predicted).toBeUndefined()
    expect(ahead.predicted).toBe(POINTS[1].predictedPrice)
    expect(ahead.fit).toBeUndefined()
  })

  it('joins the fitted line to the forecast so they do not break at now', () => {
    const rows = predictionChartRows(makeBatch([FIT_POINT, ...POINTS]))
    const join = rows.find((row) => row.timeMs === FIT_POINT.timeMs)!

    expect(join.predicted).toBe(join.fit)
  })

  /**
   * The candles and the fit come from different services and need not end on
   * the same bucket. Handing over from the last *fitted* row keeps the line
   * continuous when the fit stops short.
   */
  it('hands over from the last fitted bucket, not the last candle', () => {
    const hour = 60 * 60 * 1000
    const stale = makePoint({
      timeMs: Date.UTC(2024, 5, 15, 11),
      predictedPrice: 63_100,
    })
    const laterCandle = makeCandle({
      timeMs: Date.UTC(2024, 5, 15, 11) + hour,
      close: 63_900,
    })

    const rows = predictionChartRows(makeBatch([stale, ...POINTS]), [
      laterCandle,
    ])
    const fitted = rows.find((row) => row.timeMs === stale.timeMs)!
    const trailing = rows.find((row) => row.timeMs === laterCandle.timeMs)!

    expect(fitted.predicted).toBe(63_100)
    expect(trailing.predicted).toBeUndefined()
  })

  it('falls back to the last close when the model has no fit to join from', () => {
    const candle = makeCandle({ timeMs: Date.UTC(2024, 5, 15, 12), close: 63_450 })
    const rows = predictionChartRows(makeBatch(), [candle])
    const join = rows.find((row) => row.timeMs === candle.timeMs)!

    expect(join.predicted).toBe(63_450)
  })

  it('emits rows in time order however the inputs arrive', () => {
    const rows = predictionChartRows(makeBatch([...POINTS].reverse()), [
      makeCandle({ timeMs: Date.UTC(2024, 5, 15, 11) }),
    ])

    expect(rows.map((row) => row.timeMs)).toEqual(
      [...rows].sort((a, b) => a.timeMs - b.timeMs).map((row) => row.timeMs),
    )
  })

  /**
   * The two queries read the clock separately and a real candle is stamped
   * with its bucket start, so their timestamps agree on the hour, not the
   * millisecond. Keying on the raw instant left every candle in a row of its
   * own beside an empty one for the fit, halving the history on screen.
   */
  it('merges a candle and a fit point that are seconds apart', () => {
    const hour = 60 * 60 * 1000
    const base = Date.UTC(2024, 5, 15, 8)
    const fit = [0, 1, 2].map((index) =>
      makePoint({
        timeMs: base + index * hour,
        predictedPrice: 63_000 + index,
      }),
    )
    const drifted = [0, 1, 2].map((index) =>
      makeCandle({ timeMs: base + index * hour + 1_400 }),
    )

    const rows = predictionChartRows(makeBatch([...fit, ...POINTS]), drifted)
    const history = rows.filter((row) => row.kind === 'history')

    expect(history).toHaveLength(3)
    expect(history.every((row) => row.candle && row.fit != null)).toBe(true)
  })

  it('shades only the forecast half, where the legend applies', () => {
    const rows = predictionChartRows(makeBatch([FIT_POINT, ...POINTS]))
    const banded = rows.filter((row) => row.band)

    expect(banded.every((row) => row.kind === 'forecast' || row === rows[0])).toBe(
      true,
    )
    expect(rows.filter((row) => row.kind === 'forecast' && !row.band)).toEqual([])
  })

  it('opens the cone from a point rather than starting it already wide', () => {
    const rows = predictionChartRows(makeBatch([FIT_POINT, ...POINTS]))
    const join = rows.find((row) => row.timeMs === FIT_POINT.timeMs)!

    expect(join.band).toEqual([join.fit, join.fit])
  })

  /**
   * The history and forecast queries read the clock a moment apart, so the
   * newest candle can carry a timestamp a few milliseconds past
   * `prediction_time`. It is still a traded candle, not a projection.
   */
  it('files a candle stamped just past the boundary as history', () => {
    const boundaryCandle = makeCandle({ timeMs: BOUNDARY_MS + 120 })
    const rows = predictionChartRows(makeBatch([FIT_POINT, ...POINTS]), [
      boundaryCandle,
    ])
    const row = rows.find((r) => r.candle)!

    expect(row.kind).toBe('history')
    expect(rows.filter((r) => r.kind === 'forecast')).toHaveLength(POINTS.length)
  })

  it('still plots a candle the model has no value for', () => {
    const orphan = makeCandle({ timeMs: Date.UTC(2024, 5, 15, 9) })
    const rows = predictionChartRows(makeBatch(), [orphan])
    const row = rows.find((r) => r.timeMs === orphan.timeMs)!

    expect(row.candle).toEqual([orphan.low, orphan.high])
    expect(row.fit).toBeUndefined()
  })
})

describe('inferStepMs', () => {
  it('reads the cadence as the smallest gap in the series', () => {
    const hour = 60 * 60 * 1000

    expect(inferStepMs([0, hour, 2 * hour, 5 * hour])).toBe(hour)
  })

  it('ignores duplicates', () => {
    expect(inferStepMs([10, 10, 20])).toBe(10)
  })

  it('has no cadence to report from a single point', () => {
    expect(inferStepMs([42])).toBe(0)
    expect(inferStepMs([])).toBe(0)
  })
})

describe('forecastStartMs', () => {
  it('reports where the model stops describing the past', () => {
    const rows = predictionChartRows(makeBatch([FIT_POINT, ...POINTS]))

    expect(forecastStartMs(rows)).toBe(POINTS[0].timeMs)
  })

  it('has no boundary to report without a forecast', () => {
    expect(forecastStartMs(predictionChartRows(makeBatch([FIT_POINT])))).toBeNull()
  })
})

describe('predictionKeyLevels', () => {
  it('takes the widest bounds across the batch', () => {
    expect(predictionKeyLevels(POINTS)).toEqual({ high: 64_900, low: 63_400 })
  })

  it('has no levels to report for an empty batch', () => {
    expect(predictionKeyLevels([])).toBeNull()
  })
})

describe('predictionYDomain', () => {
  it('pads past the widest bounds so the band clears the plot edges', () => {
    const domain = predictionYDomain(POINTS, null)!

    expect(domain[0]).toBeLessThan(63_400)
    expect(domain[1]).toBeGreaterThan(64_900)
  })

  it('stretches to keep the current price in view', () => {
    const domain = predictionYDomain(POINTS, 60_000)!

    expect(domain[0]).toBeLessThan(60_000)
  })

  it('makes room for the candles behind the forecast', () => {
    const domain = predictionYDomain(POINTS, null, CANDLES)!

    expect(domain[0]).toBeLessThan(62_900)
  })

  it('still fits the candles when there is no forecast yet', () => {
    const domain = predictionYDomain([], null, CANDLES)!

    expect(domain[0]).toBeLessThan(62_900)
    expect(domain[1]).toBeGreaterThan(63_400)
  })

  it('leaves the domain to Recharts when there are no points', () => {
    expect(predictionYDomain([], 64_000)).toBeUndefined()
  })
})

describe('usesCompactTicks', () => {
  it('keeps full dollars on a span where k-rounding would repeat a tick', () => {
    expect(usesCompactTicks([63_000, 66_000])).toBe(false)
  })

  it('rounds to thousands once the span is wide enough to stay distinct', () => {
    expect(usesCompactTicks([50_000, 70_000])).toBe(true)
  })

  it('defaults to rounded ticks when Recharts picks the domain', () => {
    expect(usesCompactTicks(undefined)).toBe(true)
  })
})

describe('predictionBandWidthPercent', () => {
  it('averages the band width relative to the predicted price', () => {
    const points = [
      makePoint({ predictedPrice: 100, lowerBound: 99, upperBound: 101 }),
      makePoint({ predictedPrice: 100, lowerBound: 98, upperBound: 102 }),
    ]

    expect(predictionBandWidthPercent(points)).toBe(3)
  })

  it('is zero for an empty batch', () => {
    expect(predictionBandWidthPercent([])).toBe(0)
  })
})

describe('predictionBandWidth', () => {
  it('reads a tight band as narrow and a broad one as wide', () => {
    expect(predictionBandWidth(NARROW_BAND_MAX_PERCENT - 0.1)).toBe('narrow')
    expect(predictionBandWidth(NARROW_BAND_MAX_PERCENT)).toBe('medium')
    expect(predictionBandWidth(MEDIUM_BAND_MAX_PERCENT - 0.1)).toBe('medium')
    expect(predictionBandWidth(MEDIUM_BAND_MAX_PERCENT)).toBe('wide')
  })
})

describe('changeFromCurrentPercent', () => {
  const prediction = { currentPrice: 64_000 } as BtcPrediction

  it('measures a point against the batch anchor price', () => {
    expect(changeFromCurrentPercent(prediction, 64_640)).toBeCloseTo(1, 5)
  })

  it('has no baseline to measure against with no current price', () => {
    expect(
      changeFromCurrentPercent({ currentPrice: null } as BtcPrediction, 64_000),
    ).toBeNull()
  })
})
