import { apiUrl } from '@/lib/apiConfig'
import { toRegimeVisualIndicator } from '@/lib/regimeDisplay'
import type {
  CurrentRegime,
  CurrentRegimeResponse,
  RegimeSource,
} from '@/types/regime'

/** Real endpoint on the data service (see `app/api/regime.py`). */
export const CURRENT_REGIME_PATH = '/api/v1/regimes/current'

export function currentRegimeQueryKey() {
  return ['regimes', 'current'] as const
}

const MOCK_LATENCY_MS = 200

/** `CURRENT_REGIME_UPDATE_HOUR_UTC` — the service reclassifies at 01:00 UTC. */
const REGIME_UPDATE_HOUR_UTC = 1

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** Wire -> UI mapping; the only piece that survives the endpoint moving. */
export function mapCurrentRegime(
  response: CurrentRegimeResponse,
  source: RegimeSource = 'live',
): CurrentRegime {
  return {
    source,
    id: response.id,
    regimeType: response.regime_type,
    confidence: response.confidence,
    visualIndicator: toRegimeVisualIndicator(response.visual_indicator),
    identifiedAt: response.identified_at,
    expiresAt: response.expires_at,
  }
}

/** Most recent 01:00 UTC at or before `nowMs`, matching the service's job. */
export function lastRegimeUpdateAt(nowMs: number) {
  const identified = new Date(nowMs)
  identified.setUTCHours(REGIME_UPDATE_HOUR_UTC, 0, 0, 0)

  if (identified.getTime() > nowMs) {
    identified.setUTCDate(identified.getUTCDate() - 1)
  }

  return identified
}

export function buildMockCurrentRegime(nowMs: number): CurrentRegimeResponse {
  const identifiedAt = lastRegimeUpdateAt(nowMs)
  const expiresAt = new Date(identifiedAt)
  expiresAt.setUTCDate(expiresAt.getUTCDate() + 1)

  return {
    id: 1,
    regime_type: 'rising_rates',
    confidence: 72,
    visual_indicator: 'bear',
    identified_at: identifiedAt.toISOString(),
    expires_at: expiresAt.toISOString(),
  }
}

/** Stand-in classification for a frontend-only run, labelled as simulated. */
export async function simulateCurrentRegime(
  nowMs = Date.now(),
): Promise<CurrentRegime> {
  await delay(MOCK_LATENCY_MS)

  return mapCurrentRegime(buildMockCurrentRegime(nowMs), 'simulated')
}

/**
 * Current macro regime from the data service.
 *
 * With no backend configured the app runs on simulated data so it still works
 * standalone; with one configured a failed request throws rather than passing
 * an invented classification off as the market's actual state.
 *
 * `null` is the one non-error empty case: the endpoint 404s until the
 * classification job has run at least once, which is "not classified yet",
 * not a failure the reader should see as broken.
 */
export async function fetchCurrentRegime(
  nowMs = Date.now(),
): Promise<CurrentRegime | null> {
  const url = apiUrl(CURRENT_REGIME_PATH)

  if (!url) {
    return simulateCurrentRegime(nowMs)
  }

  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })

  if (response.status === 404) {
    return null
  }

  if (!response.ok) {
    throw new Error(`Regime request failed with ${response.status}`)
  }

  return mapCurrentRegime(
    (await response.json()) as CurrentRegimeResponse,
    'live',
  )
}
