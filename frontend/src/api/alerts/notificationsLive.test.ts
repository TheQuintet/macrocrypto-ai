import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ALERTS_USER_ID } from '@/constants/alerts'
import type {
  InAppNotification,
  NotificationResponse,
} from '@/types/alerts/notifications'

const GATEWAY_BASE = 'http://localhost:8000'
const NOTIFICATIONS_URL = `${GATEWAY_BASE}/api/v1/macro/notifications`
const ALERT_NOTIFICATIONS_URL = `${GATEWAY_BASE}/api/v1/notifications`

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
    axiosMock.get.mockImplementation(async (url: string) =>
      url === ALERT_NOTIFICATIONS_URL
        ? { data: LIVE_LIST }
        : { data: { ...LIVE_LIST, total: 0, notifications: [] } },
    )
    const { fetchNotifications } = await loadApi()

    const response = await fetchNotifications(ALERTS_USER_ID)

    expect(axiosMock.get).toHaveBeenCalledWith(NOTIFICATIONS_URL, {
      params: { limit: 50 },
      headers: { Accept: 'application/json' },
    })
    expect(response.notifications[0]?.id).toBe(LIVE_NOTIFICATION.id)
  })

  it('merges macro and price-alert lists newest first', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.get.mockImplementation(async (url: string) =>
      url === ALERT_NOTIFICATIONS_URL
        ? { data: { total: 1, notifications: [LIVE_NOTIFICATION] } }
        : {
            data: {
              total: 1,
              limit: 50,
              offset: 0,
              notifications: [
                { id: 'macro-1', event_name: 'CPI release', sent_at: '2026-09-01T12:00:00.000Z' },
              ],
            },
          },
    )
    const { fetchNotifications } = await loadApi()

    const response = await fetchNotifications(ALERTS_USER_ID)

    expect(response.total).toBe(2)
    expect(
      response.notifications.map(({ id, source }) => ({ id, source })),
    ).toEqual([
      { id: 'macro-1', source: 'macro' },
      { id: LIVE_NOTIFICATION.id, source: 'alerts' },
    ])
  })

  it('keeps the price-alert list when the macro list fails', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.get.mockImplementation(async (url: string) => {
      if (url === NOTIFICATIONS_URL) throw new Error('macro down')
      return { data: { total: 1, notifications: [LIVE_NOTIFICATION] } }
    })
    const { fetchNotifications } = await loadApi()

    const response = await fetchNotifications(ALERTS_USER_ID)

    expect(response.notifications.map((item) => item.id)).toEqual([
      LIVE_NOTIFICATION.id,
    ])
  })

  it('marks a notification read on the list it came from', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.put.mockResolvedValue({ data: {} })
    const { markNotificationAsRead } = await loadApi()

    await markNotificationAsRead({
      id: 'price-1',
      source: 'alerts',
      notification_type: 'price_alert',
    })
    await markNotificationAsRead({
      id: 'macro-1',
      source: 'macro',
      notification_type: 'macro_alert',
    })

    expect(axiosMock.put.mock.calls.map(([url]) => url)).toEqual([
      `${ALERT_NOTIFICATIONS_URL}/price-1/read`,
      `${NOTIFICATIONS_URL}/macro-1/read`,
    ])
  })

  it('marks all read on both lists and sums the counts', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.post.mockImplementation(async (url: string) => ({
      data: { count: url === ALERT_NOTIFICATIONS_URL + '/read-all' ? 3 : 2 },
    }))
    const { markAllNotificationsAsRead } = await loadApi()

    const response = await markAllNotificationsAsRead(ALERTS_USER_ID)

    expect(response.count).toBe(5)
  })

  it('fails mark all read when either list fails', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.post.mockImplementation(async (url: string) => {
      if (url === `${NOTIFICATIONS_URL}/read-all`) throw new Error('macro down')
      return { data: { count: 3 } }
    })
    const { markAllNotificationsAsRead } = await loadApi()

    await expect(markAllNotificationsAsRead(ALERTS_USER_ID)).rejects.toThrow(
      'macro down',
    )
  })

  it('surfaces a failed mark read instead of simulating it', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.put.mockRejectedValue(new Error('not found'))
    const { markNotificationAsRead } = await loadApi()

    await expect(
      markNotificationAsRead({
        id: 'price-1',
        source: 'alerts',
        notification_type: 'price_alert',
      }),
    ).rejects.toThrow('not found')
  })

  it('routes a row without a source by its notification type', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.put.mockResolvedValue({ data: {} })
    const { markNotificationAsRead } = await loadApi()

    await markNotificationAsRead({ id: 'price-1', notification_type: 'price_alert' })
    await markNotificationAsRead({ id: 'macro-1', notification_type: 'macro_alert' })

    expect(axiosMock.put.mock.calls.map(([url]) => url)).toEqual([
      `${ALERT_NOTIFICATIONS_URL}/price-1/read`,
      `${NOTIFICATIONS_URL}/macro-1/read`,
    ])
  })

  it('maps the macro notification wire onto the inbox row', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.get.mockResolvedValue({
      data: {
        total: 1,
        limit: 50,
        offset: 0,
        notifications: [
          {
            id: 'macro-1',
            event_name: 'CPI release',
            description: 'Inflation print',
            read: false,
            sent_at: '2026-09-01T12:00:00.000Z',
          },
        ],
      },
    })
    const { fetchNotifications } = await loadApi()

    const response = await fetchNotifications(ALERTS_USER_ID)

    expect(response.notifications[0]).toMatchObject({
      id: 'macro-1',
      title: 'CPI release',
      message: 'Inflation print',
      notification_type: 'macro_alert',
      created_at: '2026-09-01T12:00:00.000Z',
      read: false,
    })
  })

  it('reads naive backend timestamps as UTC', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    axiosMock.get.mockImplementation(async (url: string) => ({
      data:
        url === ALERT_NOTIFICATIONS_URL
          ? {
              total: 1,
              notifications: [
                { ...LIVE_NOTIFICATION, created_at: '2026-10-09T09:17:49.146017' },
              ],
            }
          : { total: 0, notifications: [] },
    }))
    const { fetchNotifications } = await loadApi()

    const response = await fetchNotifications(ALERTS_USER_ID)

    expect(response.notifications[0]?.created_at).toBe(
      '2026-10-09T09:17:49.146017Z',
    )
  })

  it('pages the merged list rather than each source', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', GATEWAY_BASE)
    const row = (id: string, hour: number) => ({
      ...LIVE_NOTIFICATION,
      id,
      created_at: `2026-10-09T${String(hour).padStart(2, '0')}:00:00Z`,
    })
    axiosMock.get.mockImplementation(async (url: string) => ({
      data:
        url === ALERT_NOTIFICATIONS_URL
          ? { total: 2, notifications: [row('price-10', 10), row('price-8', 8)] }
          : { total: 2, notifications: [row('macro-9', 9), row('macro-7', 7)] },
    }))
    const { fetchNotifications } = await loadApi()

    const response = await fetchNotifications(ALERTS_USER_ID, {
      limit: 2,
      offset: 1,
    })

    expect(axiosMock.get).toHaveBeenCalledWith(NOTIFICATIONS_URL, {
      params: { limit: 3 },
      headers: { Accept: 'application/json' },
    })
    expect(response.notifications.map((item) => item.id)).toEqual([
      'macro-9',
      'price-8',
    ])
  })
})
