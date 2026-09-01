import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { NotificationItem } from '@/components/alerts/notifications/NotificationItem'
import { ALERTS_USER_ID } from '@/constants/alerts'
import { createTestQueryClient } from '@/test/renderWithQuery'
import type { InAppNotification } from '@/types/alerts/notifications'

export function renderNotificationItem(
  notification: InAppNotification,
  initialPath = '/alerts',
) {
  const queryClient = createTestQueryClient()
  const router = createMemoryRouter(
    [
      {
        path: '/',
        element: <div>Price chart</div>,
      },
      {
        path: '/alerts',
        element: (
          <NotificationItem
            notification={notification}
            userId={ALERTS_USER_ID}
          />
        ),
      },
      {
        path: '/forecasts',
        element: <div>Forecasts</div>,
      },
      {
        path: '/macro',
        element: <div>Macro indicators</div>,
      },
    ],
    { initialEntries: [initialPath] },
  )

  const view = render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )

  return { view, router, queryClient }
}

export async function clickNotification(user: UserEvent, title: string) {
  await user.click(
    screen.getByRole('button', {
      name: (accessibleName) => accessibleName.includes(title),
    }),
  )
}

export function expectPath(
  router: ReturnType<typeof createMemoryRouter>,
  path: string,
) {
  expect(router.state.location.pathname).toBe(path)
}
