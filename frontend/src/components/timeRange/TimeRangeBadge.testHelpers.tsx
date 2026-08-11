import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import { TimeRangeBadge } from '@/components/timeRange/TimeRangeBadge'

export function renderTimeRangeBadge() {
  return render(<TimeRangeBadge />)
}

export function expectBadgeShows(range: string) {
  expect(screen.getByText(/showing data for/i)).toHaveTextContent(range)
}
