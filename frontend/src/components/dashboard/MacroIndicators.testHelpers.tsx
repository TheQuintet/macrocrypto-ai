import { render, screen } from '@testing-library/react';
import { MacroIndicators } from './MacroIndicators';
import type { MacroIndicator } from './MacroIndicators';

export const mockIndicators: MacroIndicator[] = [
  {
    indicator_name: 'CPI',
    time: new Date().toISOString(),
    current_value: 307.2,
    previous_value: 306.5,
    change_percent: 0.23,
    trend: '↑',
    source: 'fred',
  },
  {
    indicator_name: 'FEDFUNDS',
    time: new Date().toISOString(),
    current_value: 5.5,
    previous_value: 5.5,
    change_percent: 0.0,
    trend: '→',
    source: 'fred',
  },
  {
    indicator_name: 'UNEMPLOYMENT',
    time: new Date().toISOString(),
    current_value: 4.1,
    previous_value: 4.2,
    change_percent: -2.38,
    trend: '↓',
    source: 'fred',
  },
  {
    indicator_name: 'GDP',
    time: new Date().toISOString(),
    current_value: 32475.21,
    previous_value: 31865.721,
    change_percent: 1.91,
    trend: '↑',
    source: 'fred',
  },
];

export function renderMacroIndicators(
  props: Partial<React.ComponentProps<typeof MacroIndicators>> = {}
) {
  return render(
    <MacroIndicators 
      indicators={mockIndicators} 
      isLoading={false}
      error={null}
      {...props} 
    />
  );
}

// Note: This helper is not currently used in tests, but kept for future use
export function getCardByIndicatorName(name: string) {
  // Use screen from @testing-library/react (already imported)
  const element = screen.getByText(name);
  return element.closest('[data-slot="card"]');
}

export function getChangeElement(card: Element | null | undefined) {
  return card?.querySelector('.text-sm.font-medium');
}