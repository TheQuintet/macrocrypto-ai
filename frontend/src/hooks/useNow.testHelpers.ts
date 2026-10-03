import { act, renderHook } from '@testing-library/react'
import { vi } from 'vitest'
import { useNow } from '@/hooks/useNow'

export function renderNow(intervalMs?: number) {
  return renderHook(() => useNow(intervalMs))
}

/** Let the wall clock run on, firing any refresh that falls due. */
export function advanceClock(ms: number) {
  act(() => {
    vi.advanceTimersByTime(ms)
  })
}
