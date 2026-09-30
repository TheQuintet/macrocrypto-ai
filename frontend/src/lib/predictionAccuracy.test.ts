import { describe, expect, it } from 'vitest'
import {
  ACCURACY_PLACEHOLDER,
  accuracyMetricLabel,
  accuracyScore,
  accuracyWarningMessages,
  formatAccuracyPercent,
  formatAccuracyPeriod,
  formatErrorPercent,
  formatModelName,
  formatThresholdRule,
  formatThresholdValue,
  formatUsdMiss,
  historyScore,
  marketConditionDotClass,
  scoreTarget,
  scoreThreshold,
  thresholdTone,
  thresholdToneClass,
} from '@/lib/predictionAccuracy'
import { makeAccuracyThreshold } from '@/api/predictions/predictionAccuracy.testHelpers'

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
  it('colours markets the way the regime badges do', () => {
    expect(marketConditionDotClass('bull')).toBe('bg-positive')
    expect(marketConditionDotClass('bear')).toBe('bg-negative')
    expect(marketConditionDotClass('neutral')).toBe('bg-warning')
    expect(marketConditionDotClass('volatile')).toBe('bg-market-volatile')
  })

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
