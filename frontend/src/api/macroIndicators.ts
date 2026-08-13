import type { MacroIndicator } from '@/components/dashboard/MacroIndicators';

export async function fetchMacroIndicators(): Promise<MacroIndicator[]> {
  const response = await fetch('/api/v1/indicators');
  
  if (!response.ok) {
    throw new Error(`Failed to fetch indicators: ${response.statusText}`);
  }
  
  const data = await response.json();
  return data.indicators || [];
}