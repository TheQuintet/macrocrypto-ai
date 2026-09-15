import { useEffect, useRef, useState } from 'react'

/**
 * Measured width of an element, for charts that need an explicit pixel width.
 *
 * Recharts can size itself with `ResponsiveContainer`, but the existing charts
 * here measure and pass a width, and mixing the two inside one page makes the
 * layouts behave differently at the same breakpoint.
 */
export function useContainerWidth(fallbackWidth: number) {
  const ref = useRef<HTMLDivElement | null>(null)
  const [width, setWidth] = useState(fallbackWidth)

  useEffect(() => {
    const element = ref.current

    if (!element) {
      return
    }

    const syncWidth = () => {
      const measured = element.clientWidth

      if (measured > 0) {
        setWidth(measured)
      }
    }

    syncWidth()

    const observer = new ResizeObserver(syncWidth)
    observer.observe(element)

    return () => observer.disconnect()
  }, [])

  return { ref, width }
}
