import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MAIN_INDICATOR_NAMES } from '@/api/macroIndicators';
import { MacroIndicators } from './MacroIndicators';
import { renderMacroIndicators } from './MacroIndicators.testHelpers';

describe('MacroIndicators', () => {
  it('renders all indicators with their values', () => {
    renderMacroIndicators();
    
    expect(screen.getByText('CPI')).toBeInTheDocument();
    expect(screen.getByText('FEDFUNDS')).toBeInTheDocument();
    expect(screen.getByText('UNEMPLOYMENT')).toBeInTheDocument();
    expect(screen.getByText('GDP')).toBeInTheDocument();
    
    expect(screen.getAllByText('307.20')[0]).toBeInTheDocument();
    expect(screen.getAllByText('5.50')[0]).toBeInTheDocument();
    expect(screen.getAllByText('4.10')[0]).toBeInTheDocument();
    expect(screen.getAllByText('32475.21')[0]).toBeInTheDocument();
  });

  it('displays previous values correctly', () => {
    renderMacroIndicators();
    
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

    const cpiChange = screen.getAllByText(/\+0.23%/);
    expect(cpiChange[0]).toHaveClass('text-red-500');

    const gdpChange = screen.getAllByText(/\+1.91%/);
    expect(gdpChange[0]).toHaveClass('text-green-500');

    const unemploymentChange = screen.getAllByText(/-2.38%/);
    expect(unemploymentChange[0]).toHaveClass('text-green-500');

    const neutralChanges = screen.getAllByText(/0.00%/);
    expect(neutralChanges[0]).toHaveClass('text-muted-foreground');
  });

  // ============================================
  // RESPONSIVE TESTS (All Passing)
  // ============================================

  describe('Responsive Design', () => {
    it('has responsive grid layout classes', () => {
      const { container } = renderMacroIndicators();
      
      const grid = container.firstChild;
      expect(grid).toBeInTheDocument();
      
      expect(grid).toHaveClass('grid');
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('sm:grid-cols-2');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('has responsive gap spacing', () => {
      const { container } = renderMacroIndicators();
      const grid = container.firstChild;
      
      expect(grid).toHaveClass('gap-3');
      expect(grid).toHaveClass('sm:gap-4');
      expect(grid).toHaveClass('lg:gap-6');
    });

    it('has responsive text sizes', () => {
      renderMacroIndicators();
      
      const values = screen.getAllByText(/[0-9]+\.[0-9]+/);
      const firstValue = values[0];
      
      expect(firstValue).toHaveClass('text-xl');
      expect(firstValue).toHaveClass('sm:text-2xl');
      expect(firstValue).toHaveClass('lg:text-3xl');
    });

    it('has responsive card padding', () => {
      const { container } = renderMacroIndicators();
      
      const cardContents = container.querySelectorAll('[data-slot="card-content"]');
      expect(cardContents.length).toBeGreaterThan(0);
      
      const firstCard = cardContents[0];
      expect(firstCard).toHaveClass('p-3');
      expect(firstCard).toHaveClass('sm:p-4');
      expect(firstCard).toHaveClass('lg:p-5');
    });

    it('has touch-manipulation for mobile', () => {
      const { container } = renderMacroIndicators();
      
      const cards = container.querySelectorAll('[data-slot="card"]');
      expect(cards.length).toBeGreaterThan(0);
      
      const firstCard = cards[0];
      expect(firstCard).toHaveClass('touch-manipulation');
    });

    // ✅ FIXED: Checks the parent div instead of the span
    it('has responsive text for metadata', () => {
      renderMacroIndicators();
      
      const previousTexts = screen.getAllByText(/Previous:/);
      expect(previousTexts.length).toBeGreaterThan(0);
      
      // The parent div has the text classes, not the span itself
      const firstPreviousText = previousTexts[0];
      const parentDiv = firstPreviousText.closest('div');
      expect(parentDiv).toBeInTheDocument();
      expect(parentDiv).toHaveClass('text-xs');
      expect(parentDiv).toHaveClass('sm:text-sm');
      
      // Check titles have responsive classes
      const titles = screen.getAllByText(/CPI|FEDFUNDS|UNEMPLOYMENT|GDP/);
      const firstTitle = titles[0];
      expect(firstTitle).toHaveClass('text-xs');
      expect(firstTitle).toHaveClass('sm:text-sm');
    });

    it('maintains no horizontal overflow', () => {
      const { container } = renderMacroIndicators();
      
      const root = container.firstChild;
      expect(root).not.toHaveClass('overflow-x-auto');
    });
  });
});