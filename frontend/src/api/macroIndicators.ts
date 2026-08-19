import type { MacroIndicator } from '@/types/macroIndicators';

/** Names as returned by GET /api/v1/indicators (data-service / FRED collector). */
const MAIN_INDICATORS = new Set([
  'cpi',
  'federal_funds_rate',
  'gdp',
]);

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
