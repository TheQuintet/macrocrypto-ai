import { describe, expect, it } from 'vitest'
import {
  CANDLE_INTERVAL_OPTIONS,
  INTERVAL_DURATION_MS,
} from '@/components/dashboard/lib/chartInterval'

describe('CANDLE_INTERVAL_OPTIONS', () => {
  it('offers daily and weekly candle views', () => {
    expect(CANDLE_INTERVAL_OPTIONS.map((option) => option.value)).toEqual([
      '1d',
      '1w',
    ])
  })
})

describe('INTERVAL_DURATION_MS', () => {
  it('sizes weekly buckets as seven daily buckets', () => {
    expect(INTERVAL_DURATION_MS['1w']).toBe(INTERVAL_DURATION_MS['1d'] * 7)
  })
})
