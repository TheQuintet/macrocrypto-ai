import type { MacroIndicator } from '@/types/macroIndicators';

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

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Real gateway: GET /api/v1/indicators */
export async function fetchMacroIndicatorsFromApi(): Promise<MacroIndicator[]> {
  const response = await fetch('/api/v1/indicators');

  if (!response.ok) {
    throw new Error(`Failed to fetch indicators: ${response.statusText}`);
  }

  const data = await response.json();

  return (data.indicators || []).filter((indicator: MacroIndicator) =>
    MAIN_INDICATORS.has(indicator.indicator_name.toLowerCase()),
  );
}

const mockIndicators: MacroIndicator[] = [
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
];

/** Simulated indicators API, shaped like the real response. */
export async function fetchMockMacroIndicators(): Promise<MacroIndicator[]> {
  await delay(MOCK_LATENCY_MS);
  return mockIndicators.map((indicator) => ({ ...indicator }));
}

export const fetchMacroIndicators = USE_MOCK_MACRO_INDICATORS
  ? fetchMockMacroIndicators
  : fetchMacroIndicatorsFromApi
