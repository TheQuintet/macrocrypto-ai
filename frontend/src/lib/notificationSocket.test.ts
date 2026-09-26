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

  it('uses the simulated socket when the gateway is unset', async () => {
    const { createNotificationSocket } = await loadSocket()

    expect(createNotificationSocket('user-1')).toBeTypeOf('function')
  })

  it('does not open a stream when the gateway is configured', async () => {
    vi.stubEnv('VITE_API_GATEWAY_BASE_URL', 'http://localhost:8000')
    vi.resetModules()
    const { createNotificationSocket } = await loadSocket()

    expect(createNotificationSocket('user-1')).toBeNull()
  })
})
