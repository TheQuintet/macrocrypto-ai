import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { PredictionAlertTable } from '../PredictionAlertTable';
import { PredictionAlertForm } from '../PredictionAlertForm';
import { predictionAlertApi } from '@/api/alerts/predictionAlerts';

vi.mock('@/api/alerts/predictionAlerts');

describe('PredictionAlertResponsive', () => {
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
      name: 'Test Alert',
      description: 'Test Description',
      notify_in_app: true,
      notify_email: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ];

  const mockOnDelete = vi.fn();
  const mockOnEdit = vi.fn();
  const mockOnToggleStatus = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(predictionAlertApi.getHistory).mockResolvedValue({
      history: [],
      total: 0,
      page: 1,
      totalPages: 0,
    });
  });

  afterEach(() => {
    // Reset viewport
    Object.defineProperty(window, 'innerWidth', { value: 1920, writable: true });
    window.dispatchEvent(new Event('resize'));
  });

  it('should render table on mobile viewport', () => {
    Object.defineProperty(window, 'innerWidth', { value: 375, writable: true });
    window.dispatchEvent(new Event('resize'));

    render(
      <PredictionAlertTable
        alerts={mockAlerts}
        onDelete={mockOnDelete}
        onEdit={mockOnEdit}
        onToggleStatus={mockOnToggleStatus}
      />
    );

    expect(screen.getByText('Test Alert')).toBeInTheDocument();
    expect(screen.getByText('24h')).toBeInTheDocument();
  });

  it('should render table on desktop viewport', () => {
    Object.defineProperty(window, 'innerWidth', { value: 1920, writable: true });
    window.dispatchEvent(new Event('resize'));

    render(
      <PredictionAlertTable
        alerts={mockAlerts}
        onDelete={mockOnDelete}
        onEdit={mockOnEdit}
        onToggleStatus={mockOnToggleStatus}
      />
    );

    const testAlerts = screen.getAllByText('Test Alert');
    expect(testAlerts.length).toBeGreaterThan(0);
  });

  it('should render form on mobile viewport', () => {
    const mockProps = {
      open: true,
      onOpenChange: vi.fn(),
      userId: 'test-user',
      onSubmit: vi.fn(),
      isLoading: false,
    };

    Object.defineProperty(window, 'innerWidth', { value: 375, writable: true });
    window.dispatchEvent(new Event('resize'));

    render(<PredictionAlertForm {...mockProps} />);

    expect(screen.getByText('New prediction alert')).toBeInTheDocument();
  });
});
