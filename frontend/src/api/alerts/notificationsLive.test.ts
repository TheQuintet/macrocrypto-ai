import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ALERTS_USER_ID } from '@/constants/alerts'
import type {
  InAppNotification,
  NotificationResponse,
} from '@/types/alerts/notifications'

const GATEWAY_BASE = 'http://localhost:8000'
const NOTIFICATIONS_URL = `${GATEWAY_BASE}/api/v1/notifications`

const LIVE_NOTIFICATION: InAppNotification = {
  id: 'live-notification-id',
  user_id: ALERTS_USER_ID,
  alert_id: null,
  title: 'Live price alert',
  message: 'BTC crossed $72,000',
  notification_type: 'price_alert',
  data: null,
  action_url: '/',
  read: false,
  is_archived: false,
  created_at: '2026-08-31T08:00:00.000Z',
  read_at: null,
}

const LIVE_LIST: NotificationResponse = {
  total: 1,
  limit: 50,
  offset: 0,
  notifications: [LIVE_NOTIFICATION],
}

const axiosMock = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
}))

vi.mock('axios', () => ({
  default: axiosMock,
}))

async function loadApi() {
  return import('@/api/alerts/notifications')
}

describe('notification API', () => {
  beforeEach(() => {
    vi.resetModules()
    axiosMock.get.mockReset()
    axiosMock.post.mockReset()
    axiosMock.put.mockReset()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('does not call the gateway when it is unset', async () => {
    const { fetchNotifications, fetchUnreadNotificationCount } = await loadApi()

    await Promise.all([
      fetchNotifications(ALERTS_USER_ID),
      fetchUnreadNotificationCount(ALERTS_USER_ID),
    ])

    expect(axiosMock.get).not.toHaveBeenCalled()
  })

  it('lists notifications from the gateway when it is configured', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.get.mockResolvedValue({ data: LIVE_LIST })
    const { fetchNotifications } = await loadApi()

    const response = await fetchNotifications(ALERTS_USER_ID)

    expect(axiosMock.get).toHaveBeenCalledWith(NOTIFICATIONS_URL, {
      params: { user_id: ALERTS_USER_ID },
      headers: { Accept: 'application/json' },
    })
    expect(response.notifications[0]?.id).toBe(LIVE_NOTIFICATION.id)
  })
})
