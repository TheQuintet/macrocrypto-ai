import { test, type APIRequestContext } from '@playwright/test'

/** Must match `VITE_API_GATEWAY_BASE_URL` passed to the Vite dev server. */
export const gatewayBaseUrl =
  process.env.VITE_API_GATEWAY_BASE_URL?.replace(/\/$/, '') ??
  'http://127.0.0.1:8000'

export async function isGatewayAvailable(
  request: APIRequestContext,
): Promise<boolean> {
  try {
    const response = await request.get(`${gatewayBaseUrl}/health`, {
      timeout: 5_000,
    })
    return response.ok()
  } catch {
    return false
  }
}

export async function skipUnlessGatewayAvailable(
  request: APIRequestContext,
): Promise<void> {
  const available = await isGatewayAvailable(request)
  test.skip(
    !available,
    `API gateway not reachable at ${gatewayBaseUrl}. ` +
      'Start compose (gateway on :8000) and run with ' +
      'VITE_API_GATEWAY_BASE_URL=http://127.0.0.1:8000 npm run test:e2e:system',
  )
}
