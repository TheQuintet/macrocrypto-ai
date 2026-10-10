import { isApiGatewayConfigured } from '@/lib/apiConfig'

/**
 * Notification REST follows the API gateway. Unset → simulated inbox, no
 * HTTP. Set → live only; a failed request throws rather than substituting
 * fake notifications. Price-alert CRUD does not use this helper.
 */
export async function withSimulatedFallback<T>(
  live: () => Promise<T>,
  simulate: () => Promise<T>,
): Promise<T> {
  if (!isApiGatewayConfigured()) {
    return simulate()
  }

  return live()
}
