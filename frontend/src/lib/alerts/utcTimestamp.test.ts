import { describe, expect, it } from 'vitest'
import { asUtcTimestamp } from '@/lib/alerts/utcTimestamp'

describe('asUtcTimestamp', () => {
  it('marks a naive backend datetime as UTC', () => {
    expect(asUtcTimestamp('2026-10-09T09:17:49.146017')).toBe(
      '2026-10-09T09:17:49.146017Z',
    )
  })

  it.each([
    '2026-10-09T09:17:49Z',
    '2026-10-09T09:17:49.146+00:00',
    '2026-10-09T12:17:49+0300',
    '2026-10-09',
    '',
  ])('leaves %j unchanged', (value) => {
    expect(asUtcTimestamp(value)).toBe(value)
  })
})
