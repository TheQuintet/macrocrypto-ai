import { BTC_PRICE_PATH } from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import type {
  BtcPriceSnapshot,
  BtcPriceSnapshotResponse,
  PriceSource,
} from '@/types/btcPrice'

export function btcPriceSnapshotQueryKey() {
  return ['btc-price-snapshot'] as const
}

const MOCK_LATENCY_MS = 180
const BASE_PRICE = 82_000

/** Snapshot cadence — matches the 5s Redis TTL on the real price endpoint. */
export const PRICE_SNAPSHOT_TICK_MS = 5_000

/** Reference closes the service derives its change windows from. */
const REFERENCE_PRICE_24H = 81_100
const REFERENCE_PRICE_7D = 78_400

/** Every 11th tick moves more than 1% so the flash effect is exercisable. */
const JOLT_EVERY_TICKS = 11
const JOLT_RATIO = 0.015

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function roundCents(value: number) {
  return Math.round(value * 100) / 100
}

/** Wire -> UI mapping; the only piece that survives the real endpoint landing. */
export function mapBtcPriceSnapshot(
  response: BtcPriceSnapshotResponse,
  source: PriceSource = 'live',
): BtcPriceSnapshot {
  return {
    source,
    currentPrice: response.current_price,
    change24h: response.change_24h,
    change24hPercent: response.change_24h_percent,
    high24h: response.high_24h,
    low24h: response.low_24h,
    volume24h: response.volume_24h,
    change7d: response.change_7d,
    change7dPercent: response.change_7d_percent,
    updatedAt: response.updated_at,
  }
}

/** Deterministic price for a moment in time — same input, same output. */
export function mockBtcPriceAt(nowMs: number) {
  const tick = Math.floor(nowMs / PRICE_SNAPSHOT_TICK_MS)
  const wave = Math.sin(tick / 7) * 400 + Math.cos(tick / 23) * 150
  const jolt =
    tick % JOLT_EVERY_TICKS === 0
      ? (tick % (JOLT_EVERY_TICKS * 2) === 0 ? 1 : -1) * BASE_PRICE * JOLT_RATIO
      : 0

  return roundCents(BASE_PRICE + wave + jolt)
}

function percentOf(change: number, reference: number) {
  return roundCents((change / reference) * 100)
}

/** Simulated snapshot in the service's own wire shape. */
export function buildMockBtcPriceSnapshot(
  nowMs: number,
): BtcPriceSnapshotResponse {
  const currentPrice = mockBtcPriceAt(nowMs)
  const change24h = roundCents(currentPrice - REFERENCE_PRICE_24H)
  const change7d = roundCents(currentPrice - REFERENCE_PRICE_7D)

  return {
    current_price: currentPrice,
    change_24h: change24h,
    change_24h_percent: percentOf(change24h, REFERENCE_PRICE_24H),
    high_24h: roundCents(currentPrice + 780),
    low_24h: roundCents(currentPrice - 640),
    volume_24h: 24_180.42,
    change_7d: change7d,
    change_7d_percent: percentOf(change7d, REFERENCE_PRICE_7D),
    updated_at: new Date(nowMs).toISOString(),
  }
}

/** Stand-in snapshot for a frontend-only run, labelled as simulated. */
export async function simulateBtcPriceSnapshot(
  nowMs = Date.now(),
): Promise<BtcPriceSnapshot> {
  await delay(MOCK_LATENCY_MS)

  return mapBtcPriceSnapshot(buildMockBtcPriceSnapshot(nowMs), 'simulated')
}

/**
 * Current BTC snapshot from the data service.
 *
 * With no backend configured the app runs on simulated data so it still works
 * standalone. When a backend *is* configured a failed request throws rather
 * than quietly substituting fake prices — the card's error state is the honest
 * answer there, and silently showing invented numbers next to a "Live" badge
 * would not be.
 */
export async function fetchBtcPriceSnapshot(
  nowMs = Date.now(),
): Promise<BtcPriceSnapshot> {
  const url = apiUrl(BTC_PRICE_PATH)

  if (!url) {
    return simulateBtcPriceSnapshot(nowMs)
  }

  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`Price request failed with ${response.status}`)
  }

  return mapBtcPriceSnapshot(
    (await response.json()) as BtcPriceSnapshotResponse,
    'live',
  )
}
