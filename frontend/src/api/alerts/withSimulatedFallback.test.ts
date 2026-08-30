import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const isApiConfigured = vi.fn()

vi.mock('@/lib/apiConfig', () => ({
  isApiConfigured: () => isApiConfigured(),
}))

beforeEach(() => {
  vi.resetModules()
})

afterEach(() => {
  isApiConfigured.mockReset()
})

describe('withSimulatedFallback', () => {
  it('uses simulated data when no backend is configured', async () => {
    isApiConfigured.mockReturnValue(false)
    const { withSimulatedFallback } = await import('./withSimulatedFallback')
    const live = vi.fn()
    const simulate = vi.fn().mockResolvedValue('simulated')

    await expect(withSimulatedFallback(live, simulate)).resolves.toBe('simulated')
    expect(live).not.toHaveBeenCalled()
  })

  it('uses the live response when the backend answers', async () => {
    isApiConfigured.mockReturnValue(true)
    const { withSimulatedFallback } = await import('./withSimulatedFallback')
    const live = vi.fn().mockResolvedValue('live')
    const simulate = vi.fn()

    await expect(withSimulatedFallback(live, simulate)).resolves.toBe('live')
    expect(simulate).not.toHaveBeenCalled()
  })

  it('falls back to simulated data when the live request fails', async () => {
    isApiConfigured.mockReturnValue(true)
    const { withSimulatedFallback } = await import('./withSimulatedFallback')
    const live = vi.fn().mockRejectedValue(new Error('offline'))
    const simulate = vi.fn().mockResolvedValue('simulated')

    await expect(withSimulatedFallback(live, simulate)).resolves.toBe(
      'simulated',
    )
  })
})
