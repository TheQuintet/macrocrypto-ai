import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { PriceAlertForm } from '../PriceAlertForm';
import { mockAlert } from './testHelpers';

describe('PriceAlertForm', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
    userId: 'b5e2102c-c4ac-46f9-95c3-2a3c389399a9',
    editingAlert: null,
    onSubmit: vi.fn().mockResolvedValue(undefined),
    isLoading: false,
  };

  it('renders create form correctly', () => {
    render(<PriceAlertForm {...defaultProps} />);

    expect(screen.getByText('Create Price Alert')).toBeInTheDocument();
    expect(screen.getByLabelText(/Threshold Price/i)).toBeInTheDocument();
    const createButtons = screen.getAllByText('Create Alert');
    expect(createButtons.length).toBeGreaterThan(0);
  });

  it('renders edit form correctly', () => {
    render(
      <PriceAlertForm
        {...defaultProps}
        editingAlert={mockAlert}
        open={true}
        onOpenChange={vi.fn()}
        userId="b5e2102c-c4ac-46f9-95c3-2a3c389399a9"
        onSubmit={vi.fn()}
      />
    );

    expect(screen.getByText('Edit Price Alert')).toBeInTheDocument();
    expect(screen.getByDisplayValue('85000')).toBeInTheDocument();
    const updateButtons = screen.getAllByText('Update Alert');
    expect(updateButtons.length).toBeGreaterThan(0);
  });

  it('shows validation errors for empty fields', async () => {
    render(<PriceAlertForm {...defaultProps} />);

    const submitButtons = screen.getAllByText('Create Alert');
    fireEvent.click(submitButtons[0]);

    // Wait for validation error
    const errorMessage = await screen.findByText('Threshold must be greater than 0');
    expect(errorMessage).toBeInTheDocument();
  });

  it('calls onSubmit with form data', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<PriceAlertForm {...defaultProps} onSubmit={onSubmit} />);

    // Fill in threshold price
    const thresholdInput = screen.getByLabelText(/Threshold Price/i);
    fireEvent.change(thresholdInput, { target: { value: '85000' } });
    
    // Find the submit button and click it
    const submitButtons = screen.getAllByText('Create Alert');
    fireEvent.click(submitButtons[0]);

    // Wait for onSubmit to be called
    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalled();
    }, { timeout: 2000 });
  });
});