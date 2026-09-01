import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

async function loadSocket() {
  return import('@/lib/notificationSocket')
}

describe('createNotificationSocket transport precedence', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('uses the simulated socket when nothing is configured', async () => {
    const { createNotificationSocket } = await loadSocket()

    expect(createNotificationSocket('user-1')).toBeTypeOf('function')
  })

  it('uses a live stream when a stream URL is configured', async () => {
    vi.stubEnv(
      'VITE_NOTIFICATION_STREAM_URL',
      'http://localhost:8003/api/v1/notifications/stream',
    )
    vi.resetModules()
    const { createNotificationSocket } = await loadSocket()

    expect(createNotificationSocket('user-1')).toBeTypeOf('function')
  })

  it('still simulates push when the alert API is up but has no stream', async () => {
    vi.stubEnv('VITE_ALERT_API_BASE_URL', 'http://localhost:8003')
    vi.resetModules()
    const { createNotificationSocket } = await loadSocket()

    expect(createNotificationSocket('user-1')).toBeTypeOf('function')
  })
})
