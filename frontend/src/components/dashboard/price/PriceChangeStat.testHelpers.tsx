import { render, screen, within } from '@testing-library/react'
import { expect } from 'vitest'
import { PRICE_PLACEHOLDER } from '@/components/dashboard/lib/priceFormat'
import { PriceChangeStat } from '@/components/dashboard/price/PriceChangeStat'
import type { PriceChangeWindow } from '@/types/btcPrice'

export function renderPriceChangeStat(
  changeWindow: PriceChangeWindow,
  changeAbsolute: number | null,
  changePercent: number | null,
) {
  return render(
    <PriceChangeStat
      changeWindow={changeWindow}
      changeAbsolute={changeAbsolute}
      changePercent={changePercent}
    />,
  )
}

export function getChangeStat(label: string) {
  return screen.getByRole('group', { name: label })
}

export function expectChangeValues(
  label: string,
  percentText: string,
  absoluteText: string,
) {
  const stat = getChangeStat(label)
  expect(within(stat).getByText(percentText)).toBeInTheDocument()
  expect(within(stat).getByText(absoluteText)).toBeInTheDocument()
}

/** Both the percentage and the absolute value fall back to a placeholder. */
export function expectChangeUnavailable(label: string) {
  const stat = getChangeStat(label)
  expect(within(stat).getAllByText(PRICE_PLACEHOLDER)).toHaveLength(2)
}

export function expectChangeTone(label: string, tone: 'positive' | 'negative' | 'muted') {
  const badge = getBadge(label)

  if (tone === 'muted') {
    expect(badge).toHaveClass('text-muted-foreground')
    return
  }

  expect(badge).toHaveClass(`text-${tone}`, `bg-${tone}/10`)
}

export function expectChangeArrow(label: string, direction: 'up' | 'down' | 'flat') {
  const icon = getBadge(label).querySelector('svg')
  expect(icon).toHaveClass(ARROW_CLASS[direction])
}

const ARROW_CLASS = {
  up: 'lucide-arrow-up-right',
  down: 'lucide-arrow-down-right',
  flat: 'lucide-minus',
} as const

function getBadge(label: string) {
  const badge = getChangeStat(label).querySelector('[data-slot="badge"]')
  if (!badge) {
    throw new Error(`No change badge rendered for ${label}`)
  }

  return badge
}
