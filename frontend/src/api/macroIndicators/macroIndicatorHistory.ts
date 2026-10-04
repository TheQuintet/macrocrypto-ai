import { MACRO_INDICATORS_PATH } from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import { indicatorApiPeriod } from '@/lib/macroIndicatorHistory'
import type { MacroIndicator } from '@/types/macroIndicators'
import type { TimeRange } from '@/types/preferences'
import { normalizeMacroIndicatorsFromApi } from '@/lib/macroIndicatorDisplay'
import {
  MACRO_INDICATORS_MOCK_LATENCY_MS,
  delay,
  mockLatestIndicators,
  withDataSource,
} from '@/api/macroIndicators/macroIndicatorsShared'

const DAY_MS = 24 * 60 * 60 * 1000

const HISTORY_STEPS: Record<TimeRange, { count: number; stepMs: number }> = {
  '30d': { count: 10, stepMs: 3 * DAY_MS },
  '90d': { count: 13, stepMs: 7 * DAY_MS },
  '1y': { count: 12, stepMs: 30 * DAY_MS },
  '5y': { count: 20, stepMs: 91 * DAY_MS },
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

export function macroIndicatorHistoryQueryKey(range: TimeRange) {
  return ['macro-indicator-history', range] as const
}

export function macroIndicatorHistoryPath(range: TimeRange) {
  return `${MACRO_INDICATORS_PATH}?period=${indicatorApiPeriod(range)}`
}

function roundValue(value: number) {
  return Math.round(value * 100) / 100
}

function trendFromChange(
  changePercent: number | null,
): MacroIndicator['trend'] {
  if (changePercent === null || changePercent === 0) return '→'
  return changePercent > 0 ? '↑' : '↓'
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
      dataSource: 'simulated',
    }
  })
}

/** Stand-in history series for a frontend-only run, labelled as simulated. */
export async function simulateMacroIndicatorHistory(
  range: TimeRange,
  nowMs = Date.now(),
): Promise<MacroIndicator[]> {
  await delay(MACRO_INDICATORS_MOCK_LATENCY_MS)

  return withDataSource(
    mockLatestIndicators.flatMap((indicator) =>
      buildMockHistory(indicator, range, nowMs),
    ),
    'simulated',
  )
}

/**
 * Indicator history for a selected timeframe (`30d` / `90d` / `1y` / `5y`).
 *
 * With no backend configured the app runs on simulated series so the chart
 * still works standalone. When a backend *is* configured a failed request
 * throws rather than quietly substituting fake prints.
 */
export async function fetchMacroIndicatorHistory(
  range: TimeRange,
  nowMs = Date.now(),
): Promise<MacroIndicator[]> {
  const url = apiUrl(macroIndicatorHistoryPath(range))

  if (!url) {
    return simulateMacroIndicatorHistory(range, nowMs)
  }

  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(`Indicators request failed with ${response.status}`)
  }

  const data = await response.json()
  return withDataSource(
    normalizeMacroIndicatorsFromApi(data.indicators || []),
    'live',
  )
}
