import type { MacroIndicator } from '@/types/macroIndicators'
import type { TimeRange } from '@/types/preferences'
import { indicatorApiPeriod } from '@/lib/macroIndicatorHistory'

/** Names as returned by GET /api/v1/indicators (data-service / FRED collector). */
export const MAIN_INDICATOR_NAMES = [
  'cpi',
  'federal_funds_rate',
  'gdp',
] as const

/**
 * Flip to `false` when data-service has a FRED key and
 * GET /api/v1/indicators returns data. The query hook always
 * calls `fetchMacroIndicators`.
 */
export const USE_MOCK_MACRO_INDICATORS = true

const MAIN_INDICATORS = new Set<string>(MAIN_INDICATOR_NAMES)

const MOCK_LATENCY_MS = 280
const DAY_MS = 24 * 60 * 60 * 1000

const HISTORY_STEPS: Record<TimeRange, { count: number; stepMs: number }> = {
  '30d': { count: 10, stepMs: 3 * DAY_MS },
  '90d': { count: 13, stepMs: 7 * DAY_MS },
  '1y': { count: 12, stepMs: 30 * DAY_MS },
  '5y': { count: 20, stepMs: 91 * DAY_MS },
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function macroIndicatorsQueryKey(range?: TimeRange) {
  return ['macroIndicators', range ?? 'latest'] as const
}

function indicatorsUrl(range?: TimeRange) {
  return range
    ? `/api/v1/indicators?period=${indicatorApiPeriod(range)}`
    : '/api/v1/indicators'
}

function keepMainIndicators(indicators: MacroIndicator[]) {
  return indicators.filter((indicator) =>
    MAIN_INDICATORS.has(indicator.indicator_name.toLowerCase()),
  )
}

/** Real gateway: GET /api/v1/indicators, optionally `?period=` for history. */
export async function fetchMacroIndicatorsFromApi(
  range?: TimeRange,
): Promise<MacroIndicator[]> {
  const response = await fetch(indicatorsUrl(range))

  if (!response.ok) {
    throw new Error(`Failed to fetch indicators: ${response.statusText}`)
  }

  const data = await response.json()
  return keepMainIndicators(data.indicators || [])
}

const mockLatestIndicators: MacroIndicator[] = [
  {
    indicator_name: 'cpi',
    time: '2026-07-15T00:00:00.000Z',
    current_value: 322.13,
    previous_value: 321.47,
    change_percent: 0.21,
    trend: '↑',
    source: 'fred',
  },
  {
    indicator_name: 'federal_funds_rate',
    time: '2026-08-01T00:00:00.000Z',
    current_value: 4.33,
    previous_value: 4.33,
    change_percent: 0,
    trend: '→',
    source: 'fred',
  },
  {
    indicator_name: 'gdp',
    time: '2026-06-30T00:00:00.000Z',
    current_value: 30353.9,
    previous_value: 30111.2,
    change_percent: 0.81,
    trend: '↑',
    source: 'fred',
  },
]

function roundValue(value: number) {
  return Math.round(value * 100) / 100
}

function trendFromChange(
  changePercent: number | null,
): MacroIndicator['trend'] {
  if (changePercent === null || changePercent === 0) return '→'
  return changePercent > 0 ? '↑' : '↓'
}

/**
 * Per-series mock paths. Char-code phases made CPI (316) and GDP (315)
 * nearly identical; after rebase-to-100 those lines stacked and hid CPI.
 */
const MOCK_HISTORY_SHAPE: Record<
  string,
  { frequency: number; phase: number; amplitude: number; slope: number }
> = {
  cpi: { frequency: 0.55, phase: 0.2, amplitude: 0.018, slope: 0.004 },
  federal_funds_rate: {
    frequency: 0.95,
    phase: 1.7,
    amplitude: 0.05,
    slope: -0.003,
  },
  gdp: { frequency: 0.32, phase: 2.6, amplitude: 0.01, slope: 0.007 },
}

function buildMockHistory(
  latest: MacroIndicator,
  range: TimeRange,
  endMs: number,
): MacroIndicator[] {
  const { count, stepMs } = HISTORY_STEPS[range]
  const values: number[] = [latest.current_value]
  const shape = MOCK_HISTORY_SHAPE[latest.indicator_name] ?? {
    frequency: 0.7,
    phase: 0,
    amplitude: 0.02,
    slope: 0,
  }

  for (let index = 1; index < count; index += 1) {
    const next = values[0]
    const drift =
      (Math.sin(index * shape.frequency + shape.phase) * shape.amplitude +
        shape.slope) *
      next
    values.unshift(Math.max(0.01, next - drift))
  }

  return values.map((raw, index) => {
    const time = new Date(endMs - (count - 1 - index) * stepMs).toISOString()
    const isLast = index === values.length - 1
    if (isLast) {
      return { ...latest, time }
    }

    const currentValue = roundValue(raw)
    const previousValue = index === 0 ? null : roundValue(values[index - 1])
    const changePercent =
      previousValue && previousValue !== 0
        ? roundValue(((currentValue - previousValue) / previousValue) * 100)
        : null

    return {
      indicator_name: latest.indicator_name,
      time,
      current_value: currentValue,
      previous_value: previousValue,
      change_percent: changePercent,
      trend: trendFromChange(changePercent),
      source: latest.source,
    }
  })
}

/** Simulated indicators API, shaped like the real response. */
export async function fetchMockMacroIndicators(
  range?: TimeRange,
  nowMs = Date.now(),
): Promise<MacroIndicator[]> {
  await delay(MOCK_LATENCY_MS)

  if (!range) {
    return mockLatestIndicators.map((indicator) => ({ ...indicator }))
  }

  return mockLatestIndicators.flatMap((indicator) =>
    buildMockHistory(indicator, range, nowMs),
  )
}

export const fetchMacroIndicators = USE_MOCK_MACRO_INDICATORS
  ? fetchMockMacroIndicators
  : fetchMacroIndicatorsFromApi
