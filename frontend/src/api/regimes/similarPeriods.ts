import { SIMILAR_PERIODS_PATH } from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import type {
  RegimeSource,
  SimilarPeriod,
  SimilarPeriodResponse,
  SimilarPeriods,
  SimilarPeriodsApiResponse,
} from '@/types/regime'

/** The endpoint constrains `limit` to 3–5; asking for more is a 422. */
export const SIMILAR_PERIODS_LIMIT = 5

export function similarPeriodsQueryKey() {
  return ['regimes', 'similar-periods', SIMILAR_PERIODS_LIMIT] as const
}

const MOCK_LATENCY_MS = 240

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/** Wire -> UI mapping; the only piece that survives the endpoint moving. */
export function mapSimilarPeriod(period: SimilarPeriodResponse): SimilarPeriod {
  return {
    // The service returns no id and these are computed on the fly, so the
    // window itself is the only stable identity available for a list key.
    id: `${period.period_start}_${period.period_end}`,
    periodStart: period.period_start,
    periodEnd: period.period_end,
    distance: period.distance,
    similarityScore: period.similarity_score,
    reason: period.reason,
    matchingIndicators: (period.matching_indicators ?? []).map((indicator) => ({
      indicator: indicator.indicator,
      normalizedDifference: indicator.normalized_difference,
    })),
    macroConditions: period.macro_conditions ?? {},
    btcPerformance: period.btc_performance
      ? {
          priceStart: period.btc_performance.price_start,
          priceEnd: period.btc_performance.price_end,
          returnPercent: period.btc_performance.return_percent,
          observations: period.btc_performance.observations,
        }
      : null,
  }
}

export function mapSimilarPeriods(
  response: SimilarPeriodsApiResponse,
  source: RegimeSource = 'live',
): SimilarPeriods {
  return {
    source,
    method: response?.method ?? '',
    currentConditions: response?.current_conditions ?? {},
    periods: (response?.similar_periods ?? []).map(mapSimilarPeriod),
    message: response?.message ?? null,
  }
}

/** Stand-in matches for a frontend-only run, shaped like the real payload. */
export const MOCK_SIMILAR_PERIODS: SimilarPeriodsApiResponse = {
  method: 'normalized Euclidean distance across available indicators',
  period_count: 3,
  current_conditions: {
    cpi: 3.1,
    federal_funds_rate: 5.25,
    m2_money_supply: 21_100,
    dxy: 104.2,
    ten_year_treasury: 4.25,
    gdp: 2.4,
    unemployment: 4.1,
  },
  similar_periods: [
    {
      period_start: '2018-06-01',
      period_end: '2019-01-31',
      distance: 0.18,
      similarity_score: 88.4,
      reason:
        'Policy rate near the top of its cycle with inflation easing, as now.',
      matching_indicators: [
        { indicator: 'federal_funds_rate', normalized_difference: 0.06 },
        { indicator: 'cpi', normalized_difference: 0.14 },
      ],
      macro_conditions: {
        cpi: 2.9,
        federal_funds_rate: 5.0,
        m2_money_supply: 14_200,
        dxy: 96.1,
        ten_year_treasury: 2.85,
        gdp: 2.2,
        unemployment: 3.8,
      },
      btc_performance: {
        price_start: 7_480,
        price_end: 3_690,
        return_percent: -50.7,
        observations: 245,
      },
    },
    {
      period_start: '2006-03-01',
      period_end: '2007-02-28',
      distance: 0.24,
      similarity_score: 81.2,
      reason: 'Rates held high after a tightening cycle, growth still positive.',
      matching_indicators: [
        { indicator: 'federal_funds_rate', normalized_difference: 0.09 },
        { indicator: 'gdp', normalized_difference: 0.21 },
      ],
      macro_conditions: {
        cpi: 3.4,
        federal_funds_rate: 5.25,
        m2_money_supply: 6_800,
        dxy: 85.4,
        ten_year_treasury: 4.7,
        gdp: 2.7,
        unemployment: 4.5,
      },
      btc_performance: null,
    },
    {
      period_start: '2023-01-01',
      period_end: '2023-07-31',
      distance: 0.31,
      similarity_score: 74.6,
      reason: 'Inflation falling from its peak while the policy rate plateaued.',
      matching_indicators: [
        { indicator: 'cpi', normalized_difference: 0.18 },
        { indicator: 'federal_funds_rate', normalized_difference: 0.28 },
      ],
      macro_conditions: {
        cpi: 4.1,
        federal_funds_rate: 4.75,
        m2_money_supply: 20_800,
        dxy: 102.4,
        ten_year_treasury: 3.75,
        gdp: 2.1,
        unemployment: 3.6,
      },
      btc_performance: {
        price_start: 16_600,
        price_end: 29_200,
        return_percent: 75.9,
        observations: 212,
      },
    },
  ],
}

export async function simulateSimilarPeriods(): Promise<SimilarPeriods> {
  await delay(MOCK_LATENCY_MS)

  return mapSimilarPeriods(MOCK_SIMILAR_PERIODS, 'simulated')
}

/**
 * Historical periods whose macro conditions resemble today's, via the
 * gateway when `VITE_API_GATEWAY_BASE_URL` is set.
 *
 * With no backend configured the app runs on simulated data so it still works
 * standalone; with one configured a failed request throws rather than passing
 * invented historical parallels off as analysis.
 */
export async function fetchSimilarPeriods(): Promise<SimilarPeriods> {
  const url = apiUrl(SIMILAR_PERIODS_PATH)

  if (!url) {
    return simulateSimilarPeriods()
  }

  const response = await fetch(`${url}?limit=${SIMILAR_PERIODS_LIMIT}`, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`Similar periods request failed with ${response.status}`)
  }

  const data = (await response.json()) as SimilarPeriodsApiResponse

  return mapSimilarPeriods(data, 'live')
}
