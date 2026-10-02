import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { advanceClock, renderNow } from '@/hooks/useNow.testHelpers'

const START_MS = Date.UTC(2024, 5, 15, 12)

describe('useNow', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(START_MS)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('starts at the current time', () => {
    const view = renderNow()

    expect(view.result.current).toBe(START_MS)
  })

  it('holds still between refreshes', () => {
    const view = renderNow(60_000)

    advanceClock(30_000)

    expect(view.result.current).toBe(START_MS)
  })

  it('moves on once a refresh falls due', () => {
    const view = renderNow(60_000)

    advanceClock(60_000)

    expect(view.result.current).toBe(START_MS + 60_000)
  })
})
