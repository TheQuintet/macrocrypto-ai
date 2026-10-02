import { useEffect, useState } from 'react'

/**
 * The current time, refreshed every `intervalMs`, for labels such as
 * `12 min ago` that go stale on their own while nothing else re-renders.
 */
export function useNow(intervalMs = 60_000) {
  const [nowMs, setNowMs] = useState(() => Date.now())

  useEffect(() => {
    const timer = window.setInterval(() => setNowMs(Date.now()), intervalMs)
    return () => window.clearInterval(timer)
  }, [intervalMs])

  return nowMs
}
