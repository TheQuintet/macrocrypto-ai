import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
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
    
    // Check for Skeleton components using data-slot attribute
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
    
    // Also verify they have the bg-muted class
    const skeletonWithBg = container.querySelectorAll('[data-slot="skeleton"].bg-muted');
    expect(skeletonWithBg.length).toBeGreaterThan(0);
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

  it('displays change indicators with correct colors', () => {
    renderMacroIndicators();
    
    // Check for positive change (using getAllByText since it appears multiple times)
    const positiveChanges = screen.getAllByText(/\+0.23%/);
    expect(positiveChanges.length).toBeGreaterThan(0);
    // Check first positive change has green color
    expect(positiveChanges[0]).toHaveClass('text-green-500');
    
    // Check for negative change (unemployment)
    const negativeChanges = screen.getAllByText(/-2.38%/);
    expect(negativeChanges.length).toBeGreaterThan(0);
    // Unemployment decreased → should be green (positive for this indicator)
    expect(negativeChanges[0]).toHaveClass('text-green-500');
    
    // Check for neutral change (FEDFUNDS)
    const neutralChanges = screen.getAllByText(/0.00%/);
    expect(neutralChanges.length).toBeGreaterThan(0);
    // Neutral should have muted color
    expect(neutralChanges[0]).toHaveClass('text-muted-foreground');
  });
});