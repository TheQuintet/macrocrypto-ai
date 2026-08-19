import type { MacroIndicator } from '@/types/macroIndicators';

/** Names as returned by GET /api/v1/indicators (data-service / FRED collector). */
export const MAIN_INDICATOR_NAMES = [
  'cpi',
  'federal_funds_rate',
  'gdp',
] as const

const MAIN_INDICATORS = new Set<string>(MAIN_INDICATOR_NAMES)

export async function fetchMacroIndicators(): Promise<MacroIndicator[]> {
  const response = await fetch('/api/v1/indicators');

  if (!response.ok) {
    throw new Error(`Failed to fetch indicators: ${response.statusText}`);
  }

  const data = await response.json();

  return (data.indicators || []).filter((indicator: MacroIndicator) =>
    MAIN_INDICATORS.has(indicator.indicator_name.toLowerCase()),
  );
}
