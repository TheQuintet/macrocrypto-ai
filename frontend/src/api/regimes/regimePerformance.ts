import { apiUrl } from '@/lib/apiConfig'
import type {
  RegimePerformance,
  RegimePerformanceMetricsResponse,
  RegimePerformanceMetrics,
  RegimePerformanceRow,
  RegimePerformanceRowResponse,
  RegimeSource,
  RegimeStatus,
} from '@/types/regime'

/** Real endpoint on the data service (see `app/api/regime.py`). */
export const REGIME_PERFORMANCE_PATH = '/api/v1/regimes/performance'

export function regimePerformanceQueryKey() {
  return ['regimes', 'performance'] as const
}

const MOCK_LATENCY_MS = 220

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** The endpoint sends `completed` or `active`; anything else is completed. */
function toRegimeStatus(status: string): RegimeStatus {
  return status === 'active' ? 'active' : 'completed'
}

function mapMetrics(
  metrics: RegimePerformanceMetricsResponse,
): RegimePerformanceMetrics {
  return {
    avgReturn: metrics?.avg_return ?? null,
    maxDrawdown: metrics?.max_drawdown ?? null,
    volatility: metrics?.volatility ?? null,
    sharpeRatio: metrics?.sharpe_ratio ?? null,
    btcPriceStart: metrics?.btc_price_start ?? null,
    btcPriceEnd: metrics?.btc_price_end ?? null,
  }
}

/** Wire -> UI mapping; the only piece that survives the endpoint moving. */
export function mapRegimePerformanceRow(
  row: RegimePerformanceRowResponse,
): RegimePerformanceRow {
  return {
    regimeId: row.regime_id,
    regimeType: row.regime_type,
    startDate: row.start_date,
    endDate: row.end_date,
    status: toRegimeStatus(row.status),
    performance: mapMetrics(row.performance),
  }
}

export function mapRegimePerformance(
  rows: RegimePerformanceRowResponse[],
  source: RegimeSource = 'live',
): RegimePerformance {
  return { source, rows: rows.map(mapRegimePerformanceRow) }
}

/**
 * Stand-in history for a frontend-only run.
 *
 * Shaped after the real classes rather than random noise: the bullish
 * regimes carry positive average returns and the bearish ones negative, so
 * the chart reads correctly in a demo instead of contradicting its legend.
 */
export const MOCK_REGIME_PERFORMANCE: RegimePerformanceRowResponse[] = [
  {
    regime_id: 5,
    regime_type: 'rising_rates',
    start_date: '2024-03-01',
    end_date: null,
    status: 'active',
    performance: {
      avg_return: -4.2,
      max_drawdown: -18.6,
      volatility: 41.3,
      sharpe_ratio: -0.21,
      btc_price_start: 61_400,
      btc_price_end: 58_820,
    },
  },
  {
    regime_id: 4,
    regime_type: 'growth',
    start_date: '2023-08-01',
    end_date: '2024-02-29',
    status: 'completed',
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
    regime_id: 3,
    regime_type: 'high_inflation',
    start_date: '2022-11-01',
    end_date: '2023-07-31',
    status: 'completed',
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
    regime_id: 2,
    regime_type: 'falling_rates',
    start_date: '2022-02-01',
    end_date: '2022-10-31',
    status: 'completed',
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
    regime_id: 1,
    regime_type: 'recession',
    start_date: '2021-06-01',
    end_date: '2022-01-31',
    status: 'completed',
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

export async function simulateRegimePerformance(): Promise<RegimePerformance> {
  await delay(MOCK_LATENCY_MS)

  return mapRegimePerformance(MOCK_REGIME_PERFORMANCE, 'simulated')
}

/**
 * BTC performance per macro regime from the data service.
 *
 * With no backend configured the app runs on simulated data so it still works
 * standalone; with one configured a failed request throws rather than passing
 * invented returns off as measured ones.
 */
export async function fetchRegimePerformance(): Promise<RegimePerformance> {
  const url = apiUrl(REGIME_PERFORMANCE_PATH)

  if (!url) {
    return simulateRegimePerformance()
  }

  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`Regime performance request failed with ${response.status}`)
  }

  const data = (await response.json()) as RegimePerformanceRowResponse[]

  return mapRegimePerformance(Array.isArray(data) ? data : [], 'live')
}
