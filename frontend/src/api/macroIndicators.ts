import type { MacroIndicator } from '@/components/dashboard/MacroIndicators';

// Define which indicators to show (only these 3)
const MAIN_INDICATORS = ['CPI', 'FEDFUNDS', 'gdp'];

export async function fetchMacroIndicators(): Promise<MacroIndicator[]> {
  try {
    const response = await fetch('/api/v1/indicators');
    
    if (!response.ok) {
      throw new Error(`Failed to fetch indicators: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Filter to only show CPI, FEDFUNDS, GDP
    return (data.indicators || [])
      .filter((indicator: MacroIndicator) => 
        MAIN_INDICATORS.includes(indicator.indicator_name)
      );
  } catch (error) {
    console.error('Error fetching macro indicators:', error);
    return []; // Return empty array on error
  }
}