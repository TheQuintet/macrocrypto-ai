import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ALERTS_USER_ID } from '@/constants/alerts'
import type {
  InAppNotification,
  NotificationResponse,
} from '@/types/alerts/notifications'

const ALERT_API_BASE = 'http://localhost:8003'
const NOTIFICATIONS_URL = `${ALERT_API_BASE}/api/v1/notifications`
const STREAM_URL = `${ALERT_API_BASE}/api/v1/notifications/stream`

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

  it('does not call the alert host when VITE_NOTIFICATION_STREAM_URL is unset', async () => {
    vi.stubEnv('VITE_ALERT_API_BASE_URL', ALERT_API_BASE)
    vi.stubEnv('VITE_NOTIFICATION_STREAM_URL', '')
    const { fetchNotifications, fetchUnreadNotificationCount } = await loadApi()

    await Promise.all([
      fetchNotifications(ALERTS_USER_ID),
      fetchUnreadNotificationCount(ALERTS_USER_ID),
    ])

    expect(axiosMock.get).not.toHaveBeenCalled()
  })

  it('lists notifications from the live API when the stream URL is set', async () => {
    vi.stubEnv('VITE_ALERT_API_BASE_URL', ALERT_API_BASE)
    vi.stubEnv('VITE_NOTIFICATION_STREAM_URL', STREAM_URL)
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
