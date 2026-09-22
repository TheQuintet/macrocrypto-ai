import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { PredictionAlertTable } from '../PredictionAlertTable';

describe('PredictionAlertTable', () => {
  const mockAlerts = [
    {
      id: '1',
      user_id: 'user-1',
      threshold: 5 as const,
      horizon: '24h' as const,
      confidence_change: 5,
      direction: 'both' as const,
      asset: 'BTC/USD',
      status: 'active' as const,
      one_time: false,
      name: 'Bullish Breakout',
      description: 'Strong upward movement',
      notify_in_app: true,
      notify_email: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: '2',
      user_id: 'user-1',
      threshold: 10 as const,
      horizon: '7d' as const,
      confidence_change: 8,
      direction: 'both' as const,
      asset: 'BTC/USD',
      status: 'disabled' as const,
      one_time: true,
      name: 'Major Trend Change',
      description: 'Significant 7-day changes',
      notify_in_app: true,
      notify_email: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ];

  const mockOnDelete = vi.fn();
  const mockOnEdit = vi.fn();
  const mockOnToggleStatus = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render table with alerts', () => {
    render(
      <PredictionAlertTable
        alerts={mockAlerts}
        onDelete={mockOnDelete}
        onEdit={mockOnEdit}
        onToggleStatus={mockOnToggleStatus}
      />
    );

    expect(screen.getAllByText('Bullish Breakout').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Major Trend Change').length).toBeGreaterThan(0);
    expect(screen.getAllByText('24h').length).toBeGreaterThan(0);
    expect(screen.getAllByText('7d').length).toBeGreaterThan(0);
  });

  it('should show empty state when no alerts', () => {
    render(
      <PredictionAlertTable
        alerts={[]}
        onDelete={mockOnDelete}
        onEdit={mockOnEdit}
        onToggleStatus={mockOnToggleStatus}
      />
    );

    expect(
      screen.getAllByText('No prediction alerts found matching your filters').length,
    ).toBeGreaterThan(0);
  });

  it('should call onEdit when alert row is clicked', async () => {
    const user = userEvent.setup();
    render(
      <PredictionAlertTable
        alerts={mockAlerts}
        onDelete={mockOnDelete}
        onEdit={mockOnEdit}
        onToggleStatus={mockOnToggleStatus}
      />
    );

    const alertNames = screen.getAllByText('Bullish Breakout');
    await user.click(alertNames[0]);

    expect(mockOnEdit).toHaveBeenCalledWith(mockAlerts[0]);
  });

  it('should call onDelete when delete button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <PredictionAlertTable
        alerts={mockAlerts}
        onDelete={mockOnDelete}
        onEdit={mockOnEdit}
        onToggleStatus={mockOnToggleStatus}
      />
    );

    const deleteButtons = screen.getAllByRole('button', { name: /Delete alert/i });
    await user.click(deleteButtons[0]);

    expect(mockOnDelete).toHaveBeenCalledWith(mockAlerts[0]);
  });
});
