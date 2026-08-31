import { screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { TooltipProvider } from '@/components/ui/tooltip'
import { ALERTS_USER_ID } from '@/constants/alerts'
import { routes } from '@/constants/navigation'
import { renderWithQuery } from '@/test/renderWithQuery'
import { NotificationBell } from './NotificationBell'

export function renderNotificationBell() {
  return renderWithQuery(
    <MemoryRouter>
      <TooltipProvider>
        <NotificationBell userId={ALERTS_USER_ID} />
      </TooltipProvider>
    </MemoryRouter>,
  )
}

export function getNotificationsButton() {
  return screen.getByRole('button', { name: 'Notifications' })
}

export async function openNotifications(user: UserEvent) {
  await user.click(getNotificationsButton())
}

export function expectManageAlertsLink() {
  expect(screen.getByRole('link', { name: 'Manage alerts' })).toHaveAttribute(
    'href',
    routes.alerts,
  )
}

export function expectUnreadBadge(count: string) {
  expect(screen.getByText(count)).toBeInTheDocument()
}

export function expectUnreadBell() {
  const button = getNotificationsButton()
  expect(button.querySelector('svg')).toHaveClass(
    'text-green-600',
    'dark:text-green-500',
  )
  expect(button.querySelector('[data-slot="badge"]')).toHaveClass('bg-green-600')
}

export function expectReadBell() {
  expect(getNotificationsButton().querySelector('svg')).not.toHaveClass(
    'text-green-600',
  )
}

export function expectNoUnreadBadge() {
  expect(screen.queryByText('3')).not.toBeInTheDocument()
}
