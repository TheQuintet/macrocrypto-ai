import { describe, expect, it } from 'vitest'
import {
  ACCURACY_PLACEHOLDER,
  accuracyMetricLabel,
  accuracyScore,
  accuracyScoreExplanation,
  accuracyScoreLabel,
  accuracyTrendCaption,
  comparisonMaxZoom,
  comparisonZoomPoints,
  formatComparisonSpan,
  formatTrendTarget,
  trendTargets,
  accuracyTrendGapNote,
  accuracyTrendLineLabel,
  accuracyWarningMessages,
  buildAccuracyTrend,
  formatAccuracyPercent,
  formatAccuracyPeriod,
  formatErrorPercent,
  formatModelName,
  formatPriceGap,
  formatThresholdRule,
  formatThresholdValue,
  formatUsdMiss,
  formatUsdPrice,
  historyScore,
  marketAccuracy,
  marketGrade,
  marketGradeBarClass,
  marketGradeLegend,
  marketGradeTextClass,
  scoreTarget,
  scoreThreshold,
  thresholdTone,
  thresholdToneClass,
  trendLineStyle,
  trendScoreKind,
} from '@/lib/predictionAccuracy'
import {
  makeAccuracyThreshold,
  makeMapeWarning,
  makePredictionAccuracy,
} from '@/api/predictions/predictionAccuracy.testHelpers'

describe('accuracyScore', () => {
  it('leads with directional accuracy when the service reports it', () => {
    expect(
      accuracyScore({ mae: 1, rmse: 1, mape: 1.8, directionalAccuracy: 61.5 }),
    ).toEqual({ kind: 'directional', value: 61.5 })
  })

  it('falls back to 100 minus MAPE and says so', () => {
    expect(
      accuracyScore({ mae: 1, rmse: 1, mape: 1.8, directionalAccuracy: null }),
    ).toEqual({ kind: 'price', value: 98.2 })
  })

  it('keeps the score inside 0–100 however bad the miss', () => {
    expect(
      accuracyScore({ mae: 1, rmse: 1, mape: 140, directionalAccuracy: null }),
    ).toEqual({ kind: 'price', value: 0 })
  })

  it('has no score with nothing to score from', () => {
    expect(
      accuracyScore({ mae: 1, rmse: 1, mape: null, directionalAccuracy: null }),
    ).toBeNull()
  })
})

describe('historyScore', () => {
  const point = {
    time: '2026-09-13T06:00:00Z',
    timeMs: 0,
    mape: 2,
    directionalAccuracy: 58,
    sampleSize: 24,
  }

  it('plots the same figure as the headline', () => {
    expect(historyScore(point, 'directional')).toBe(58)
    expect(historyScore(point, 'price')).toBe(98)
  })

  it('leaves a gap where a day has no value', () => {
    expect(
      historyScore({ ...point, directionalAccuracy: null }, 'directional'),
    ).toBeNull()
  })
})

describe('scoreTarget', () => {
  const thresholds = [
    makeAccuracyThreshold({ metric: 'directional_accuracy', threshold: 55 }),
    makeAccuracyThreshold({
      metric: 'mape',
      threshold: 10,
      breachDirection: 'above',
    }),
  ]

  it('reads the directional floor as is', () => {
    expect(scoreTarget('directional', thresholds)).toBe(55)
  })

  it('turns a MAPE ceiling into a floor on the price score', () => {
    expect(scoreTarget('price', thresholds)).toBe(90)
  })

  it('has no target when the service sent no matching check', () => {
    expect(scoreTarget('price', [])).toBeNull()
  })
})

describe('formatting', () => {
  it('rounds the headline to whole percent', () => {
    expect(formatAccuracyPercent(61.5)).toBe('62%')
    expect(formatAccuracyPercent(null)).toBe(ACCURACY_PLACEHOLDER)
  })

  it('keeps two places on small error percentages', () => {
    expect(formatErrorPercent(1.8)).toBe('1.80%')
  })

  it('prints a miss in whole dollars', () => {
    expect(formatUsdMiss(1_152.4)).toBe('$1,152')
    expect(formatUsdMiss(null)).toBe(ACCURACY_PLACEHOLDER)
  })

  it('names the period in days', () => {
    expect(formatAccuracyPeriod(30)).toBe('Last 30 days')
    expect(formatAccuracyPeriod(1)).toBe('Last 1 day')
  })

  it('names known model families and passes others through', () => {
    expect(formatModelName('prophet_fresh')).toBe('Prophet (fresh)')
    expect(formatModelName('xgboost_incremental')).toBe(
      'XGBoost (incremental)',
    )
    expect(formatModelName('lightgbm')).toBe('LightGBM')
    expect(formatModelName('ensemble_v2')).toBe('ensemble_v2')
  })

  it('names metrics in plain language', () => {
    expect(accuracyMetricLabel('directional_accuracy')).toBe(
      'Direction called right',
    )
    expect(accuracyMetricLabel('unknown_metric')).toBe('unknown_metric')
  })

  it('prints a check value the way the metric is shown elsewhere', () => {
    expect(formatThresholdValue(makeAccuracyThreshold({ value: 53.2 }))).toBe(
      '53%',
    )
    expect(
      formatThresholdValue(makeAccuracyThreshold({ metric: 'mape', value: 5.6 })),
    ).toBe('5.60%')
  })

  it('states each rule from the side the value must stay on', () => {
    expect(
      formatThresholdRule(
        makeAccuracyThreshold({ threshold: 55, breachDirection: 'below' }),
      ),
    ).toBe('Must stay above 55%')
    expect(
      formatThresholdRule(
        makeAccuracyThreshold({ threshold: 10, breachDirection: 'above' }),
      ),
    ).toBe('Must stay below 10%')
  })
})

describe('accuracyWarningMessages', () => {
  const quiet = { warning: false, warningCount: 0, warningThresholdDays: 3 }

  it('explains each metric the service is warning about', () => {
    expect(
      accuracyWarningMessages({
        ...quiet,
        warning: true,
        warningCount: 1,
        thresholds: [
          makeAccuracyThreshold({
            breached: true,
            warning: true,
            consecutiveDays: 4,
          }),
        ],
      }),
    ).toEqual([
      'Direction called right has been below 55% for 4 days in a row.',
    ])
  })

  it('ignores a breach the service has not yet turned into a warning', () => {
    expect(
      accuracyWarningMessages({
        ...quiet,
        thresholds: [
          makeAccuracyThreshold({
            breached: true,
            warning: false,
            consecutiveDays: 1,
          }),
        ],
      }),
    ).toEqual([])
  })

  it('still warns when the flagged metric is missing from the checks', () => {
    expect(
      accuracyWarningMessages({
        ...quiet,
        warning: true,
        warningCount: 1,
        thresholds: [],
      }),
    ).toEqual([
      'The service has flagged 1 metric outside its bound for 3+ days in a row.',
    ])
  })

  it('counts flagged metrics it cannot name alongside the ones it can', () => {
    expect(
      accuracyWarningMessages({
        ...quiet,
        warning: true,
        warningCount: 3,
        thresholds: [
          makeAccuracyThreshold({
            breached: true,
            warning: true,
            consecutiveDays: 4,
          }),
        ],
      }),
    ).toEqual([
      'Direction called right has been below 55% for 4 days in a row.',
      'The service is also flagging 2 metrics for 3+ days in a row.',
    ])
  })
})

describe('colour', () => {
  it('greens a figure inside its bound', () => {
    expect(thresholdToneClass(makeAccuracyThreshold())).toBe('text-positive')
  })

  it('ambers a figure the service is warning about', () => {
    expect(
      thresholdToneClass(
        makeAccuracyThreshold({ breached: true, warning: true }),
      ),
    ).toBe('text-warning')
  })

  it('gives the chart the same tone as the text', () => {
    expect(thresholdTone(makeAccuracyThreshold())).toBe('positive')
    expect(
      thresholdTone(makeAccuracyThreshold({ breached: true, warning: true })),
    ).toBe('warning')
  })

  it('grades the headline by the check on the same figure', () => {
    const mape = makeAccuracyThreshold({ metric: 'mape' })

    expect(scoreThreshold('price', [makeAccuracyThreshold(), mape])).toBe(
      mape,
    )
  })

  it('leaves a fresh breach and an ungraded figure uncoloured', () => {
    expect(
      thresholdToneClass(makeAccuracyThreshold({ breached: true })),
    ).toBe('')
    expect(thresholdToneClass(undefined)).toBe('')
  })
})

describe('trendScoreKind', () => {
  const directional = { mae: 1, rmse: 1, mape: 2, directionalAccuracy: 60 }
  const priceOnly = { mae: 1, rmse: 1, mape: 2, directionalAccuracy: null }

  it('plots direction only when every horizon reports it', () => {
    expect(
      trendScoreKind([
        makePredictionAccuracy({ metrics: directional }),
        makePredictionAccuracy({ horizon: '7d', metrics: directional }),
      ]),
    ).toBe('directional')
  })

  it('falls back to price accuracy for both when either lacks direction', () => {
    expect(
      trendScoreKind([
        makePredictionAccuracy({ metrics: directional }),
        makePredictionAccuracy({ horizon: '7d', metrics: priceOnly }),
      ]),
    ).toBe('price')
  })

  it('uses price accuracy with nothing scored', () => {
    expect(trendScoreKind([])).toBe('price')
  })
})

describe('buildAccuracyTrend', () => {
  const at = (day: number) => Date.UTC(2026, 8, day, 6)
  const point = (day: number, mape: number) => ({
    time: new Date(at(day)).toISOString(),
    timeMs: at(day),
    mape,
    directionalAccuracy: 60,
    sampleSize: 1,
  })

  it('merges both horizons on time, oldest first, with gaps where one is missing', () => {
    const rows = buildAccuracyTrend(
      [
        makePredictionAccuracy({ history: [point(12, 2), point(11, 3)] }),
        makePredictionAccuracy({
          horizon: '7d',
          history: [point(12, 10), point(13, 11)],
        }),
      ],
      'price',
    )

    expect(rows).toEqual([
      { timeMs: at(11), '24h': 97 },
      { timeMs: at(12), '24h': 98, '7d': 90 },
      { timeMs: at(13), '7d': 89 },
    ])
  })
})

describe('trend labels', () => {
  it('names the figure the lines plot', () => {
    expect(accuracyTrendCaption('price')).toMatch(/^Price accuracy/)
    expect(accuracyTrendCaption('directional')).toMatch(/^Direction called/)
  })

  it('names each line by its horizon', () => {
    expect(accuracyTrendLineLabel('7d')).toBe('7d forecasts')
  })

  it('keeps a fixed colour per horizon, neither of them a grade colour', () => {
    expect(trendLineStyle('24h')).toEqual({
      stroke: 'var(--chart-1)',
      swatchClass: 'bg-chart-1',
    })
    expect(trendLineStyle('7d')).toEqual({
      stroke: 'var(--indicator-gdp)',
      swatchClass: 'bg-indicator-gdp',
    })
  })

  it('draws one target where both horizons share a bound', () => {
    const targets = trendTargets(
      [
        makePredictionAccuracy(),
        makePredictionAccuracy({ horizon: '7d', thresholds: [makeMapeWarning()] }),
      ],
      'price',
    )

    expect(targets).toEqual([{ value: 90, horizons: ['24h', '7d'] }])
    expect(formatTrendTarget(targets[0])).toBe('Service target 90% (24h & 7d)')
  })

  it('draws a target per horizon where the bounds differ, none without one', () => {
    expect(
      trendTargets(
        [
          makePredictionAccuracy(),
          makePredictionAccuracy({
            horizon: '7d',
            thresholds: [makeMapeWarning({ threshold: 15 })],
          }),
          makePredictionAccuracy({ thresholds: [] }),
        ],
        'price',
      ),
    ).toEqual([
      { value: 90, horizons: ['24h'] },
      { value: 85, horizons: ['7d'] },
    ])
  })

  it('explains a missing line, and stays quiet while it loads or draws', () => {
    expect(accuracyTrendGapNote('7d', undefined, new Error('down'))).toBe(
      'The 7d line is unavailable: down',
    )
    expect(accuracyTrendGapNote('7d', null, null)).toMatch(
      /No 7d forecasts have been scored yet/,
    )
    expect(accuracyTrendGapNote('7d', undefined, null)).toBeNull()
    expect(
      accuracyTrendGapNote('7d', makePredictionAccuracy(), null),
    ).toBeNull()
  })
})

describe('marketGrade', () => {
  // The service's 10% MAPE ceiling, and an overall miss under it, so a
  // market can sit between the two.
  const bound = makeMapeWarning({ threshold: 10 })
  const overall = 9

  it('greens a market at or better than the model overall', () => {
    expect(marketGrade(8.1, overall, bound)).toBe('good')
    expect(marketGrade(9, overall, bound)).toBe('good')
  })

  it('yellows a market within the bound but worse than overall', () => {
    expect(marketGrade(9.5, overall, bound)).toBe('medium')
    expect(marketGrade(10, overall, bound)).toBe('medium')
  })

  it('reds a market beyond the service bound', () => {
    expect(marketGrade(11.88, overall, bound)).toBe('poor')
  })

  it('grades against overall only, and never red, without a bound', () => {
    expect(marketGrade(1.53, 1.8, undefined)).toBe('good')
    expect(marketGrade(40, 1.8, undefined)).toBe('medium')
  })

  it('falls back to the bound alone without an overall figure', () => {
    expect(marketGrade(4, null, bound)).toBe('good')
    expect(marketGrade(12, null, bound)).toBe('poor')
    expect(marketGrade(4, null, undefined)).toBeNull()
  })

  it('does not grade a market with no figure', () => {
    expect(marketGrade(null, overall, bound)).toBeNull()
  })

  it('maps each grade to a literal colour class', () => {
    expect(marketGradeTextClass('good')).toBe('text-positive')
    expect(marketGradeTextClass('medium')).toBe('text-warning')
    expect(marketGradeTextClass('poor')).toBe('text-negative')
    expect(marketGradeTextClass(null)).toBe('')
    expect(marketGradeBarClass('poor')).toBe('bg-negative')
    expect(marketGradeBarClass(null)).toBe('bg-muted-foreground')
  })

  it('reads a market on the headline scale, 100 minus its MAPE', () => {
    expect(marketAccuracy(1.53)).toBeCloseTo(98.47)
    expect(marketAccuracy(140)).toBe(0)
    expect(marketAccuracy(null)).toBeNull()
  })

  it('explains the colours, naming the bound only when there is one', () => {
    expect(marketGradeLegend(bound)).toMatch(/Red: .*10% bound\.$/)
    expect(marketGradeLegend(undefined)).not.toMatch(/Red/)
  })
})

describe('price formatting', () => {
  it('prints a BTC price in whole dollars', () => {
    expect(formatUsdPrice(64_100.5)).toBe('$64,101')
  })

  it('signs the gap from the forecast side', () => {
    expect(formatPriceGap(64_100.5, 63_880.2)).toBe('+$220 (+0.34%)')
    expect(formatPriceGap(63_000, 64_000)).toBe('-$1,000 (-1.56%)')
    expect(formatPriceGap(64_000, 64_000)).toBe('$0 (0.00%)')
  })
})

describe('score wording', () => {
  const metrics = { mae: 1_152.4, rmse: 1_555, mape: 1.8, directionalAccuracy: null }

  it('names which figure the headline is', () => {
    expect(accuracyScoreLabel('price')).toBe('Price accuracy')
    expect(accuracyScoreLabel('directional')).toBe('Direction accuracy')
  })

  it('puts price accuracy as how close forecasts landed, not how often right', () => {
    const text = accuracyScoreExplanation('price', metrics)

    expect(text).toBe(
      'Forecasts were within 1.80% of the real price on average (about $1,152).',
    )
    expect(text).not.toMatch(/of the time|right/)
  })

  it('drops the dollar figure when there is none', () => {
    expect(accuracyScoreExplanation('price', { ...metrics, mae: null })).toBe(
      'Forecasts were within 1.80% of the real price on average.',
    )
  })

  it('keeps the "right N% of the time" wording for direction only', () => {
    expect(
      accuracyScoreExplanation('directional', {
        ...metrics,
        directionalAccuracy: 61.5,
      }),
    ).toBe('Called the direction right 62% of the time.')
  })
})

describe('comparison zoom', () => {
  const hourMs = 60 * 60 * 1000
  const points = Array.from({ length: 97 }, (_, index) => ({
    time: '',
    timeMs: index * hourMs,
    predicted: 1,
    actual: 1,
    marketCondition: null,
  }))

  it('shows every forecast fully zoomed out', () => {
    expect(comparisonZoomPoints(points, 0)).toBe(points)
  })

  it('keeps the latest half of the span with each step in', () => {
    expect(comparisonZoomPoints(points, 1)).toHaveLength(49)
    expect(comparisonZoomPoints(points, 2)).toHaveLength(25)
    expect(comparisonZoomPoints(points, 2).at(-1)).toBe(points.at(-1))
  })

  it('stops zooming in while a handful of forecasts is still on screen', () => {
    expect(comparisonMaxZoom(points)).toBe(4)
    expect(comparisonMaxZoom(points.slice(0, 9))).toBe(1)
    expect(comparisonMaxZoom([])).toBe(0)
  })

  it('names the span on screen in whole days', () => {
    expect(formatComparisonSpan(points)).toBe('Showing the last 4 days')
    expect(formatComparisonSpan(points.slice(0, 13))).toBe(
      'Showing the last 1 day',
    )
    expect(formatComparisonSpan(points.slice(0, 1))).toBe(
      'Showing one forecast',
    )
  })
})
