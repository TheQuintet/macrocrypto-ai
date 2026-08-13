import { act, renderHook } from '@testing-library/react'
import { vi } from 'vitest'
import { PRICE_FLASH_DURATION_MS } from '@/components/dashboard/lib/priceFlash'
import { usePriceFlash } from '@/hooks/usePriceFlash'

export function renderPriceFlash(initialPrice: number | null) {
  return renderHook((price: number | null) => usePriceFlash(price), {
    initialProps: initialPrice,
  })
}

type PriceFlashView = ReturnType<typeof renderPriceFlash>

/** Feed the hook a newly received price. */
export function observePrice(view: PriceFlashView, price: number | null) {
  act(() => {
    view.rerender(price)
  })
}

export function advancePastFlash() {
  act(() => {
    vi.advanceTimersByTime(PRICE_FLASH_DURATION_MS)
  })
}
