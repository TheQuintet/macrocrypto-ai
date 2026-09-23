import { isApiGatewayConfigured } from '@/lib/apiConfig'

/**
 * Notification REST follows the API gateway. Unset → simulated inbox, no
 * HTTP. Set → try live, and if that request fails (routes still missing)
 * fall back so the bell still works. Price-alert CRUD does not use this.
 */
export async function withSimulatedFallback<T>(
  live: () => Promise<T>,
  simulate: () => Promise<T>,
): Promise<T> {
  if (!isApiGatewayConfigured()) {
    return simulate()
  }

  try {
    return await live()
  } catch {
    return simulate()
  }
}
