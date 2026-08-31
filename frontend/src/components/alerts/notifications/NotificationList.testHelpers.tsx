import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { NotificationList } from '@/components/alerts/notifications/NotificationList'
import { ALERTS_USER_ID } from '@/constants/alerts'
import { createTestQueryClient } from '@/test/renderWithQuery'

export function renderNotificationList() {
  const queryClient = createTestQueryClient()
  const view = render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <NotificationList userId={ALERTS_USER_ID} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return { view, queryClient }
}

export async function clickMarkAllAsRead(user: UserEvent) {
  await user.click(screen.getByRole('button', { name: 'Mark all as read' }))
}

export function expectNewestFirst(titles: string[]) {
  const buttons = screen.getAllByRole('listitem')
  const rendered = buttons.map((item) => item.textContent ?? '')
  for (const [index, title] of titles.entries()) {
    expect(rendered[index]).toContain(title)
  }
}
