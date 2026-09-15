import { apiUrl } from '@/lib/apiConfig'
import type {
  RegimeHistory,
  RegimeHistoryRow,
  RegimeHistoryRowResponse,
  RegimePerformanceMetrics,
  RegimePerformanceMetricsResponse,
  RegimeSource,
} from '@/types/regime'

/** Real endpoint on the data service (see `app/api/regime.py`). */
export const REGIME_HISTORY_PATH = '/api/v1/regimes'

export function regimeHistoryQueryKey() {
  return ['regimes', 'history'] as const
}

const MOCK_LATENCY_MS = 210

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function mapMetrics(
  metrics: RegimePerformanceMetricsResponse | null,
): RegimePerformanceMetrics | null {
  if (!metrics) {
    return null
  }

  return {
    avgReturn: metrics.avg_return ?? null,
    maxDrawdown: metrics.max_drawdown ?? null,
    volatility: metrics.volatility ?? null,
    sharpeRatio: metrics.sharpe_ratio ?? null,
    btcPriceStart: metrics.btc_price_start ?? null,
    btcPriceEnd: metrics.btc_price_end ?? null,
  }
}

/** Wire -> UI mapping; the only piece that survives the endpoint moving. */
export function mapRegimeHistoryRow(
  row: RegimeHistoryRowResponse,
): RegimeHistoryRow {
  return {
    id: row.id,
    regimeType: row.regime_type,
    startDate: row.start_date,
    endDate: row.end_date,
    // No end date is how the service marks the regime still running; there is
    // no separate status field on this endpoint.
    isCurrent: row.end_date == null,
    performance: mapMetrics(row.performance),
  }
}

export function mapRegimeHistory(
  rows: RegimeHistoryRowResponse[],
  source: RegimeSource = 'live',
): RegimeHistory {
  return { source, rows: rows.map(mapRegimeHistoryRow) }
}

/** Stand-in history for a frontend-only run, spanning a few years. */
export const MOCK_REGIME_HISTORY: RegimeHistoryRowResponse[] = [
  {
    id: 5,
    regime_type: 'rising_rates',
    start_date: '2024-03-01',
    end_date: null,
    performance: null,
  },
  {
    id: 4,
    regime_type: 'growth',
    start_date: '2023-08-01',
    end_date: '2024-02-29',
    performance: {
      avg_return: 28.4,
      max_drawdown: -11.2,
      volatility: 36.8,
      sharpe_ratio: 1.42,
      btc_price_start: 47_800,
      btc_price_end: 61_400,
    },
  },
  {
    id: 3,
    regime_type: 'high_inflation',
    start_date: '2022-11-01',
    end_date: '2023-07-31',
    performance: {
      avg_return: -12.7,
      max_drawdown: -31.5,
      volatility: 52.1,
      sharpe_ratio: -0.44,
      btc_price_start: 54_700,
      btc_price_end: 47_800,
    },
  },
  {
    id: 2,
    regime_type: 'falling_rates',
    start_date: '2022-02-01',
    end_date: '2022-10-31',
    performance: {
      avg_return: 16.9,
      max_drawdown: -14.8,
      volatility: 38.2,
      sharpe_ratio: 0.87,
      btc_price_start: 46_800,
      btc_price_end: 54_700,
    },
  },
  {
    id: 1,
    regime_type: 'recession',
    start_date: '2021-06-01',
    end_date: '2022-01-31',
    performance: {
      avg_return: -21.3,
      max_drawdown: -44.7,
      volatility: 61.5,
      sharpe_ratio: -0.68,
      btc_price_start: 59_500,
      btc_price_end: 46_800,
    },
  },
]

export async function simulateRegimeHistory(): Promise<RegimeHistory> {
  await delay(MOCK_LATENCY_MS)

  return mapRegimeHistory(MOCK_REGIME_HISTORY, 'simulated')
}

/**
 * Historical macro regimes from the data service.
 *
 * With no backend configured the app runs on simulated data so it still works
 * standalone; with one configured a failed request throws rather than drawing
 * an invented history of the market.
 */
export async function fetchRegimeHistory(): Promise<RegimeHistory> {
  const url = apiUrl(REGIME_HISTORY_PATH)

  if (!url) {
    return simulateRegimeHistory()
  }

  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`Regime history request failed with ${response.status}`)
  }

  const data = (await response.json()) as RegimeHistoryRowResponse[]

  return mapRegimeHistory(Array.isArray(data) ? data : [], 'live')
}
