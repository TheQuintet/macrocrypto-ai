import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MAIN_INDICATOR_NAMES } from '@/api/macroIndicators';
import { MacroIndicators } from './MacroIndicators';
import { renderMacroIndicators } from './MacroIndicators.testHelpers';

describe('MacroIndicators', () => {
  it('renders all indicators with their values', () => {
    renderMacroIndicators();
    
    // Check indicators exist by name
    expect(screen.getByText('CPI')).toBeInTheDocument();
    expect(screen.getByText('FEDFUNDS')).toBeInTheDocument();
    expect(screen.getByText('UNEMPLOYMENT')).toBeInTheDocument();
    expect(screen.getByText('GDP')).toBeInTheDocument();
    
    // Check values are displayed (using getAllByText since values might appear multiple times)
    expect(screen.getAllByText('307.20')[0]).toBeInTheDocument();
    expect(screen.getAllByText('5.50')[0]).toBeInTheDocument();
    expect(screen.getAllByText('4.10')[0]).toBeInTheDocument();
    expect(screen.getAllByText('32475.21')[0]).toBeInTheDocument();
  });

  it('displays previous values correctly', () => {
    renderMacroIndicators();
    
    // Check that previous values appear in the component
    // Use getAllByText and check first occurrence
    const prevValues = screen.getAllByText(/306.50/);
    expect(prevValues.length).toBeGreaterThan(0);
    expect(prevValues[0]).toBeInTheDocument();
    
    const prevFedFunds = screen.getAllByText(/5.50/);
    expect(prevFedFunds.length).toBeGreaterThan(0);
    expect(prevFedFunds[0]).toBeInTheDocument();
  });

  it('shows loading skeletons when isLoading is true', () => {
    const { container } = render(<MacroIndicators indicators={[]} isLoading={true} />);

    const cards = container.querySelectorAll('[data-slot="card"]');
    expect(cards).toHaveLength(MAIN_INDICATOR_NAMES.length);

    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
    expect(container.querySelectorAll('[data-slot="skeleton"].bg-muted').length).toBeGreaterThan(0);
  });

  it('shows error message when error is provided', () => {
    const error = new Error('Failed to fetch data');
    render(<MacroIndicators indicators={[]} error={error} />);
    expect(screen.getByText('Failed to load macroeconomic indicators')).toBeInTheDocument();
  });

  it('shows empty state when no indicators are provided', () => {
    render(<MacroIndicators indicators={[]} />);
    expect(screen.getByText('No macroeconomic data available')).toBeInTheDocument();
  });

  it('displays trend arrows with percentage change', () => {
    renderMacroIndicators();

    expect(screen.getAllByText(/↑ \+0\.23%/)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/→ 0\.00%/)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/↓ -2\.38%/)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/↑ \+1\.91%/)[0]).toBeInTheDocument();
  });

  it('displays change indicators with BTC-positive/negative colors', () => {
    renderMacroIndicators();

    // CPI up → negative for BTC → red
    const cpiChange = screen.getAllByText(/\+0.23%/);
    expect(cpiChange[0]).toHaveClass('text-red-500');

    // GDP up → positive for BTC → green
    const gdpChange = screen.getAllByText(/\+1.91%/);
    expect(gdpChange[0]).toHaveClass('text-green-500');

    // Unemployment down → positive for BTC → green
    const unemploymentChange = screen.getAllByText(/-2.38%/);
    expect(unemploymentChange[0]).toHaveClass('text-green-500');

    // Fed funds unchanged → muted
    const neutralChanges = screen.getAllByText(/0.00%/);
    expect(neutralChanges[0]).toHaveClass('text-muted-foreground');
  });
});