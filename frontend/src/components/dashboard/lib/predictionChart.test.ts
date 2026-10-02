import { describe, expect, it } from 'vitest'
import {
  changeFromCurrentPercent,
  inferStepMs,
  forecastStartMs,
  formatConfidencePercent,
  formatForecastAge,
  formatPredictionTick,
  formatPredictionTime,
  MEDIUM_BAND_MAX_PERCENT,
  NARROW_BAND_MAX_PERCENT,
  predictionBandWidth,
  predictionBandWidthPercent,
  predictionChartRows,
  predictionKeyLevels,
  predictionTickStepMs,
  predictionTicks,
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

const HOUR = 60 * 60 * 1000
const DAY = 24 * HOUR

describe('predictionTickStepMs', () => {
  it('steps a 24h axis in hours when there is room', () => {
    expect(predictionTickStepMs(48 * HOUR, 10, '24h')).toBe(6 * HOUR)
  })

  it('never ticks a 7d axis finer than daily, however wide the plot', () => {
    expect(predictionTickStepMs(14 * DAY, 100, '7d')).toBe(DAY)
  })

  it('coarsens the step so a narrow plot keeps to its label budget', () => {
    const step = predictionTickStepMs(14 * DAY, 4, '7d')

    expect((14 * DAY) / step).toBeLessThanOrEqual(4)
  })

  it('tops out at weekly ticks for the widest zoom', () => {
    expect(predictionTickStepMs(400 * DAY, 2, '7d')).toBe(7 * DAY)
  })
})

describe('predictionTicks', () => {
  const start = Date.UTC(2024, 5, 15, 12, 30)

  it('places sub-day ticks on whole local hours at the step', () => {
    const ticks = predictionTicks(start, start + 48 * HOUR, 6 * HOUR)

    expect(ticks.length).toBeGreaterThanOrEqual(7)
    for (const tick of ticks) {
      const date = new Date(tick)
      expect(date.getMinutes()).toBe(0)
      expect(date.getHours() % 6).toBe(0)
    }
  })

  it('places day ticks on local midnights', () => {
    const ticks = predictionTicks(start, start + 14 * DAY, DAY)

    expect(ticks).toHaveLength(14)
    for (const tick of ticks) {
      const date = new Date(tick)
      expect(date.getHours()).toBe(0)
      expect(date.getMinutes()).toBe(0)
    }
  })

  it('skips days for a multi-day step', () => {
    const ticks = predictionTicks(start, start + 14 * DAY, 7 * DAY)

    expect(ticks).toHaveLength(2)
    expect(ticks[1] - ticks[0]).toBeGreaterThanOrEqual(7 * DAY - HOUR)
  })

  it('keeps every tick inside the plotted span', () => {
    const end = start + 36 * HOUR
    const ticks = predictionTicks(start, end, 3 * HOUR)

    expect(ticks.every((tick) => tick >= start && tick <= end)).toBe(true)
  })
})

describe('formatPredictionTick', () => {
  const midday = new Date(2024, 5, 15, 13, 0).getTime()
  const midnight = new Date(2024, 5, 16, 0, 0).getTime()

  it('reads sub-day ticks as clock times', () => {
    expect(formatPredictionTick(midday, 6 * HOUR)).toMatch(/^\d{2}:\d{2}$/)
  })

  it('reads a sub-day tick at midnight as the new date', () => {
    expect(formatPredictionTick(midnight, 6 * HOUR)).toMatch(/^\d{2} \w{3}$/)
  })

  it('reads day ticks as dates', () => {
    expect(formatPredictionTick(midday, DAY)).toMatch(/^\d{2} \w{3}$/)
  })
})

describe('formatPredictionTime', () => {
  it('gives the weekday, date and hour, so a point places within a week', () => {
    const label = formatPredictionTime(new Date(2024, 5, 15, 13).getTime())

    expect(label).toMatch(/Sat/)
    expect(label).toMatch(/15 Jun/)
    expect(label).toMatch(/13:00/)
  })
})

describe('formatForecastAge', () => {
  const made = Date.UTC(2024, 5, 15, 12)

  it('reads a batch under a minute old as just made', () => {
    expect(formatForecastAge(made, made + 20_000)).toBe('just now')
  })

  it('counts minutes, then hours, then days', () => {
    expect(formatForecastAge(made, made + 12 * 60_000)).toBe('12 min ago')
    expect(formatForecastAge(made, made + 20 * HOUR)).toBe('20 h ago')
    expect(formatForecastAge(made, made + 3 * DAY)).toBe('3 d ago')
  })

  it('does not report a future age when the clocks disagree', () => {
    expect(formatForecastAge(made, made - 5_000)).toBe('just now')
  })
})

const BOUNDARY_MS = Date.UTC(2024, 5, 15, 12, 30)

/** A forward-only batch, as the endpoint returns one. */
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

/** A forecast point dated at or before `prediction_time`, as a stale batch has. */
const EARLY_POINT = makePoint({
  timeMs: Date.UTC(2024, 5, 15, 12),
  predictedPrice: 63_600,
  lowerBound: 63_500,
  upperBound: 63_700,
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

  /**
   * The endpoint never returns fitted values, so a point dated at or before
   * `prediction_time` is still a forecast — drawn, banded, and counted.
   */
  it('draws a point at or before the batch time as forecast, not fit', () => {
    const rows = predictionChartRows(makeBatch([EARLY_POINT, ...POINTS]))
    const early = rows.find((row) => row.timeMs === EARLY_POINT.timeMs)!

    expect(early.kind).toBe('forecast')
    expect(early.predicted).toBe(EARLY_POINT.predictedPrice)
    expect(early.band).toEqual([EARLY_POINT.lowerBound, EARLY_POINT.upperBound])
    expect(rows.filter((row) => row.kind === 'forecast')).toHaveLength(
      POINTS.length + 1,
    )
  })

  it('overlays a candle on the forecast hour it traded in', () => {
    const candle = makeCandle({ timeMs: EARLY_POINT.timeMs })
    const rows = predictionChartRows(makeBatch([EARLY_POINT, ...POINTS]), [
      candle,
    ])
    const merged = rows.find((row) => row.timeMs === EARLY_POINT.timeMs)!

    expect(merged.kind).toBe('forecast')
    expect(merged.candle).toEqual([candle.low, candle.high])
    expect(merged.predicted).toBe(EARLY_POINT.predictedPrice)
  })

  it('files candles before the first forecast point as history', () => {
    const candle = makeCandle({ timeMs: Date.UTC(2024, 5, 15, 11) })
    const rows = predictionChartRows(makeBatch(), [candle])
    const row = rows.find((r) => r.timeMs === candle.timeMs)!

    expect(row.kind).toBe('history')
    expect(row.lower).toBeUndefined()
  })

  it('starts the forecast line from the last close before it', () => {
    const candle = makeCandle({ timeMs: Date.UTC(2024, 5, 15, 12), close: 63_450 })
    const rows = predictionChartRows(makeBatch(), [candle])
    const join = rows.find((row) => row.timeMs === candle.timeMs)!

    expect(join.predicted).toBe(63_450)
  })

  it('opens the cone from a point rather than starting it already wide', () => {
    const candle = makeCandle({ timeMs: Date.UTC(2024, 5, 15, 12), close: 63_450 })
    const rows = predictionChartRows(makeBatch(), [candle])
    const join = rows.find((row) => row.timeMs === candle.timeMs)!

    expect(join.band).toEqual([63_450, 63_450])
  })

  it('joins nothing when there are no candles to start from', () => {
    const rows = predictionChartRows(makeBatch())

    expect(rows.every((row) => row.kind === 'forecast')).toBe(true)
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
   * The candles and the forecast come from different services, so their
   * timestamps agree on the hour, not the millisecond. Keying on the raw
   * instant would leave each candle in a row of its own beside the point.
   */
  it('merges a candle and a forecast point that are seconds apart', () => {
    const drifted = POINTS.map((point) =>
      makeCandle({ timeMs: point.timeMs + 1_400 }),
    )

    const rows = predictionChartRows(makeBatch(), drifted)

    expect(rows).toHaveLength(POINTS.length)
    expect(rows.every((row) => row.candle && row.predicted != null)).toBe(true)
  })

  it('keeps a candle stamped just before the forecast start as history', () => {
    const candle = makeCandle({ timeMs: POINTS[0].timeMs - 60 * 60 * 1000 + 120 })
    const rows = predictionChartRows(makeBatch(), [candle])
    const row = rows.find((r) => r.candle)!

    expect(row.kind).toBe('history')
    expect(rows.filter((r) => r.kind === 'forecast')).toHaveLength(POINTS.length)
  })

  it('shades every forecast row and no history row but the join', () => {
    const candles = [
      makeCandle({ timeMs: Date.UTC(2024, 5, 15, 10) }),
      makeCandle({ timeMs: Date.UTC(2024, 5, 15, 11) }),
    ]
    const rows = predictionChartRows(makeBatch(), candles)
    const bandedHistory = rows.filter(
      (row) => row.kind === 'history' && row.band,
    )

    expect(bandedHistory.map((row) => row.timeMs)).toEqual([
      Date.UTC(2024, 5, 15, 11),
    ])
    expect(rows.filter((row) => row.kind === 'forecast' && !row.band)).toEqual([])
  })

  it('still plots a candle the model has no value for', () => {
    const orphan = makeCandle({ timeMs: Date.UTC(2024, 5, 15, 9) })
    const rows = predictionChartRows(makeBatch(), [
      orphan,
      makeCandle({ timeMs: Date.UTC(2024, 5, 15, 12) }),
    ])
    const row = rows.find((r) => r.timeMs === orphan.timeMs)!

    expect(row.candle).toEqual([orphan.low, orphan.high])
    expect(row.predicted).toBeUndefined()
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
  it('reports the first forecast point, even one before the batch time', () => {
    const rows = predictionChartRows(makeBatch([EARLY_POINT, ...POINTS]))

    expect(forecastStartMs(rows)).toBe(EARLY_POINT.timeMs)
  })

  it('has no boundary to report without a forecast', () => {
    expect(
      forecastStartMs(predictionChartRows(makeBatch([]), CANDLES)),
    ).toBeNull()
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
