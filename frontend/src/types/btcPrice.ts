/**
 * Wire shape of the BTC market snapshot.
 * Real gateway: GET /api/v1/btc/price
 * Mirrors `services/data-service/app/api/schemas/price_response.py`, so every
 * field stays optional — the service returns nulls before its first tick.
 */
export type BtcPriceSnapshotResponse = {
  current_price: number | null
  change_24h: number | null
  change_24h_percent: number | null
  high_24h: number | null
  low_24h: number | null
  volume_24h: number | null
  change_7d: number | null
  change_7d_percent: number | null
  updated_at: string | null
}

/** Camel-cased snapshot used across the UI. */
export type BtcPriceSnapshot = {
  currentPrice: number | null
  change24h: number | null
  change24hPercent: number | null
  high24h: number | null
  low24h: number | null
  volume24h: number | null
  change7d: number | null
  change7dPercent: number | null
  updatedAt: string | null
}

/** Change windows rendered alongside the current price. */
export type PriceChangeWindow = '24h' | '7d'
