import { describe, expect, it } from 'vitest'
import {
  candleIntervalForTimeRange,
  isCandleIntervalAllowed,
} from '@/lib/timeRange'

describe('candleIntervalForTimeRange', () => {
  it('keeps short ranges on daily candles', () => {
    expect(candleIntervalForTimeRange('30d')).toBe('1d')
    expect(candleIntervalForTimeRange('90d')).toBe('1d')
  })

  it('uses weekly candles once the range is a year or more', () => {
    expect(candleIntervalForTimeRange('1y')).toBe('1w')
    expect(candleIntervalForTimeRange('5y')).toBe('1w')
  })
})

describe('isCandleIntervalAllowed', () => {
  it('blocks daily candles on 1y and 5y', () => {
    expect(isCandleIntervalAllowed('1y', '1d')).toBe(false)
    expect(isCandleIntervalAllowed('5y', '1d')).toBe(false)
    expect(isCandleIntervalAllowed('1y', '1w')).toBe(true)
  })

  it('allows daily or weekly on shorter ranges', () => {
    expect(isCandleIntervalAllowed('30d', '1d')).toBe(true)
    expect(isCandleIntervalAllowed('90d', '1w')).toBe(true)
  })
})
