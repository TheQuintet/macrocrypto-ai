import { describe, expect, it } from 'vitest'
import {
  formatConditionValue,
  similarPeriodIndicatorKeys,
  similarPeriodIndicatorLabel,
  SIMILAR_PERIOD_INDICATORS,
} from '@/lib/similarPeriodIndicators'
import type { SimilarPeriod } from '@/types/regime'

function period(
  macroConditions: SimilarPeriod['macroConditions'],
): SimilarPeriod {
  return {
    id: 'x',
    periodStart: '2018-01-01',
    periodEnd: '2018-02-01',
    distance: 0.2,
    similarityScore: 80,
    reason: 'test',
    matchingIndicators: [],
    macroConditions,
    btcPerformance: null,
  }
}

describe('similarPeriodIndicators', () => {
  it('always lists the engine indicators, even when the payload is thin', () => {
    expect(similarPeriodIndicatorKeys({})).toEqual([
      ...SIMILAR_PERIOD_INDICATORS,
    ])
  })

  it('appends unexpected payload keys after the engine set', () => {
    expect(similarPeriodIndicatorKeys({ cpi: 3, custom_print: 1 })).toEqual([
      ...SIMILAR_PERIOD_INDICATORS,
      'custom_print',
    ])
  })

  it('picks up keys that only appear on a historical period', () => {
    const keys = similarPeriodIndicatorKeys({}, [
      period({ custom_print: 12 }),
    ])

    expect(keys).toContain('custom_print')
  })

  it('formats missing prints as an em dash', () => {
    expect(formatConditionValue(undefined)).toBe('—')
    expect(formatConditionValue(3.1)).toBe('3.10')
  })

  it('uses the short labels the table and Today strip share', () => {
    expect(similarPeriodIndicatorLabel('federal_funds_rate')).toBe('Fed funds')
    expect(similarPeriodIndicatorLabel('ten_year_treasury')).toBe('10y')
  })
})
