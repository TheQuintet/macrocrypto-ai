import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { PredictionAlertForm } from '../PredictionAlertForm';
import { predictionAlertApi } from '@/api/alerts/predictionAlerts';

vi.mock('@/api/alerts/predictionAlerts');

describe('PredictionAlertForm', () => {
  const mockUserId = 'test-user-id';
  const mockOnSubmit = vi.fn();
  const mockOnOpenChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const defaultProps = {
    open: true,
    onOpenChange: mockOnOpenChange,
    userId: mockUserId,
    onSubmit: mockOnSubmit,
    isLoading: false,
  };

  it('should render the form when open', () => {
    render(<PredictionAlertForm {...defaultProps} />);

    expect(screen.getByText('New prediction alert')).toBeInTheDocument();
    const submitButtons = screen.getAllByRole('button', { name: 'Create alert' });
    expect(submitButtons.length).toBeGreaterThan(0);
  });

  it('should show preview when preview button is clicked', async () => {
    const user = userEvent.setup();
    const mockPreview = {
      previousPrediction: 68234.50,
      newPrediction: 70123.75,
      changePercentage: 2.77,
      confidence: 74,
      recommendation: 'Bullish shift - consider increasing exposure',
      horizon: '24h' as const,
    };

    vi.mocked(predictionAlertApi.getPreview).mockResolvedValue(mockPreview);

    render(<PredictionAlertForm {...defaultProps} />);

    const previewButtons = screen.getAllByText('Preview');
    await user.click(previewButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Prediction Change Alert')).toBeInTheDocument();
    });
  });

  it('should show edit mode when editingAlert is provided', () => {
    const editingAlert = {
      id: 'test-id',
      user_id: mockUserId,
      threshold: 5 as const,
      horizon: '24h' as const,
      confidence_change: 5,
      status: 'active' as const,
      one_time: false,
      name: 'Test Alert',
      description: 'Test Description',
      notify_in_app: true,
      notify_email: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    render(
      <PredictionAlertForm
        {...defaultProps}
        editingAlert={editingAlert}
      />
    );

    expect(screen.getByText('Edit prediction alert')).toBeInTheDocument();
    const saveButtons = screen.getAllByRole('button', { name: 'Save changes' });
    expect(saveButtons.length).toBeGreaterThan(0);
    expect(screen.getByDisplayValue('Test Alert')).toBeInTheDocument();
  });

  it('should call onOpenChange when cancel is clicked', async () => {
    const user = userEvent.setup();
    render(<PredictionAlertForm {...defaultProps} />);

    const cancelButtons = screen.getAllByText('Cancel');
    await user.click(cancelButtons[0]);

    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });
});
