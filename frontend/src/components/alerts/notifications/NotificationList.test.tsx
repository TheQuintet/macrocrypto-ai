import { cleanup, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { resetSimulatedNotifications } from '@/api/alerts/simulatedNotifications'
import {
  clickMarkAllAsRead,
  expectNewestFirst,
  renderNotificationList,
} from './NotificationList.testHelpers'

describe('NotificationList', () => {
  beforeEach(() => {
    resetSimulatedNotifications()
  })

  afterEach(() => {
    cleanup()
  })

  it('lists notifications newest first', async () => {
    renderNotificationList()

    expect(
      await screen.findByRole('heading', { name: /Unread/ }),
    ).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Read' })).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /BTC broke \$70,000/ }),
    ).toBeInTheDocument()
    expectNewestFirst([
      'BTC broke $70,000',
      'CPI print came in hot',
      'BTC hit $65,000',
      'BTC dipped under $60,000',
      '24h outlook updated',
    ])
  })

  it('marks every notification as read', async () => {
    const user = userEvent.setup()
    renderNotificationList()

    expect(
      await screen.findByRole('button', { name: 'Mark all as read' }),
    ).toBeInTheDocument()

    await clickMarkAllAsRead(user)

    await waitFor(() => {
      expect(
        screen.queryByRole('button', { name: 'Mark all as read' }),
      ).not.toBeInTheDocument()
    })
    expect(
      screen.queryByRole('button', { name: /unread/ }),
    ).not.toBeInTheDocument()
  })
})
