import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PredictionAlertPreview } from '../PredictionAlertPreview';

describe('PredictionAlertPreview', () => {
  const mockPreview = {
    previousPrediction: 68234.50,
    newPrediction: 70123.75,
    changePercentage: 2.77,
    confidence: 74,
    recommendation: 'Bullish shift - consider increasing exposure',
    horizon: '24h' as const,
  };

  it('should render preview with bullish data', () => {
    render(<PredictionAlertPreview preview={mockPreview} />);

    expect(screen.getByText('Prediction Change Alert')).toBeInTheDocument();
    expect(screen.getByText('68235')).toBeInTheDocument();
    expect(screen.getByText('70124')).toBeInTheDocument();
    expect(screen.getByText(/2\.8/)).toBeInTheDocument();
    expect(screen.getByText('74% confidence')).toBeInTheDocument();
    expect(screen.getByText('Bullish shift - consider increasing exposure')).toBeInTheDocument();
    expect(screen.getByText('24h')).toBeInTheDocument();
  });

  it('should render preview with bearish data', () => {
    const bearishPreview = {
      ...mockPreview,
      previousPrediction: 71500,
      newPrediction: 68900,
      changePercentage: -3.64,
      recommendation: 'Bearish shift - consider adjusting position',
    };

    render(<PredictionAlertPreview preview={bearishPreview} />);

    expect(screen.getByText('71500')).toBeInTheDocument();
    expect(screen.getByText('68900')).toBeInTheDocument();
    expect(screen.getByText(/3\.6/)).toBeInTheDocument();
    expect(screen.getByText('Bearish shift - consider adjusting position')).toBeInTheDocument();
  });

  it('should show loading state when isLoading is true', () => {
    render(<PredictionAlertPreview preview={null} isLoading={true} />);

    expect(screen.getByText('Generating preview...')).toBeInTheDocument();
  });

  it('should show placeholder when no preview data', () => {
    render(<PredictionAlertPreview preview={null} isLoading={false} />);

    expect(screen.getByText('Set threshold and horizon to see a preview')).toBeInTheDocument();
    expect(screen.getByText('This shows how the alert will appear when triggered')).toBeInTheDocument();
  });
});
