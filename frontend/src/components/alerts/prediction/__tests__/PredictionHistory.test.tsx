import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { PredictionHistory } from '../PredictionHistory';
import { predictionAlertApi } from '@/api/alerts/predictionAlerts';

vi.mock('@/api/alerts/predictionAlerts');

describe('PredictionHistory', () => {
  const mockUserId = 'test-user-id';
  const mockHistory = {
    history: [
      {
        id: 'h1',
        alert_id: '1',
        previous_prediction: 68234.50,
        new_prediction: 70123.75,
        change_percentage: 2.77,
        horizon: '24h' as const,
        threshold: 5 as const,
        triggered_at: '2024-01-01T00:00:00Z',
        recommendation: 'Bullish shift - consider increasing exposure',
        read: false,
      },
      {
        id: 'h2',
        alert_id: '2',
        previous_prediction: 71500,
        new_prediction: 68900,
        change_percentage: -3.64,
        horizon: '7d' as const,
        threshold: 10 as const,
        triggered_at: '2024-01-02T00:00:00Z',
        recommendation: 'Bearish shift - consider adjusting position',
        read: true,
      },
    ],
    total: 2,
    page: 1,
    totalPages: 1,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(predictionAlertApi.getHistory).mockResolvedValue(mockHistory);
    vi.mocked(predictionAlertApi.exportHistory).mockResolvedValue(new Blob(['test']));
  });

  it('should render history table with data', async () => {
    render(<PredictionHistory userId={mockUserId} />);

    await waitFor(() => {
      expect(screen.getByText('Prediction Alert History (2)')).toBeInTheDocument();
      expect(screen.getByText('68235')).toBeInTheDocument();
      expect(screen.getByText('70124')).toBeInTheDocument();
      expect(screen.getByText(/2\.8/)).toBeInTheDocument();
    });
  });

  it('should show empty state when no history', async () => {
    vi.mocked(predictionAlertApi.getHistory).mockResolvedValue({
      history: [],
      total: 0,
      page: 1,
      totalPages: 0,
    });

    render(<PredictionHistory userId={mockUserId} />);

    await waitFor(() => {
      expect(screen.getByText('No history records found')).toBeInTheDocument();
    });
  });

  it('should handle search input', async () => {
    const user = userEvent.setup();
    render(<PredictionHistory userId={mockUserId} />);

    const searchInputs = screen.getAllByPlaceholderText('Search alerts...');
    await user.type(searchInputs[0], 'Bullish');

    await waitFor(() => {
      expect(predictionAlertApi.getHistory).toHaveBeenCalledWith(
        mockUserId,
        expect.objectContaining({
          search: 'Bullish',
        })
      );
    });
  });
});
