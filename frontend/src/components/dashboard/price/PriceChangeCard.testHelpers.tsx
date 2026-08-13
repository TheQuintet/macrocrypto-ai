import { screen, waitFor, within } from '@testing-library/react'
import { expect } from 'vitest'
import { PriceChangeCard } from '@/components/dashboard/price/PriceChangeCard'
import { renderWithQuery } from '@/test/renderWithQuery'

export function renderPriceChangeCard() {
  return renderWithQuery(<PriceChangeCard />)
}

export async function expectWindowValues(
  label: string,
  percentText: string,
  absoluteText: string,
) {
  await waitFor(() => {
    const stat = screen.getByRole('group', { name: label })
    expect(within(stat).getByText(percentText)).toBeInTheDocument()
    expect(within(stat).getByText(absoluteText)).toBeInTheDocument()
  })
}

export function expectLoadingSkeletons() {
  expect(
    document.querySelectorAll('[data-slot="skeleton"]').length,
  ).toBeGreaterThan(0)
  expect(screen.queryByRole('group')).not.toBeInTheDocument()
}
