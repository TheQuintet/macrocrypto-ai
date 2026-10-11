import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const isApiGatewayConfigured = vi.fn()

vi.mock('@/lib/apiConfig', () => ({
  isApiGatewayConfigured: () => isApiGatewayConfigured(),
}))

beforeEach(() => {
  vi.resetModules()
})

afterEach(() => {
  isApiGatewayConfigured.mockReset()
})

describe('withSimulatedFallback', () => {
  it('uses simulated data when the API gateway is unset', async () => {
    isApiGatewayConfigured.mockReturnValue(false)
    const { withSimulatedFallback } = await import('./withSimulatedFallback')
    const live = vi.fn()
    const simulate = vi.fn().mockResolvedValue('simulated')

    await expect(withSimulatedFallback(live, simulate)).resolves.toBe(
      'simulated',
    )
    expect(live).not.toHaveBeenCalled()
  })

  it('uses the live response when the notification backend answers', async () => {
    isApiGatewayConfigured.mockReturnValue(true)
    const { withSimulatedFallback } = await import('./withSimulatedFallback')
    const live = vi.fn().mockResolvedValue('live')
    const simulate = vi.fn()

    await expect(withSimulatedFallback(live, simulate)).resolves.toBe('live')
    expect(simulate).not.toHaveBeenCalled()
  })

  it('propagates live request failures when the gateway is configured', async () => {
    isApiGatewayConfigured.mockReturnValue(true)
    const { withSimulatedFallback } = await import('./withSimulatedFallback')
    const live = vi.fn().mockRejectedValue(new Error('offline'))
    const simulate = vi.fn().mockResolvedValue('simulated')

    await expect(withSimulatedFallback(live, simulate)).rejects.toThrow(
      'offline',
    )
    expect(simulate).not.toHaveBeenCalled()
  })
})
