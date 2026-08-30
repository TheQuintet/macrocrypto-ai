import { cleanup, render, screen, fireEvent } from '@testing-library/react';
import { afterEach, describe, it, expect, vi } from 'vitest';
import { AlertListItem } from '../AlertListItem';
import { mockAlert } from '../price/__tests__/testHelpers';

describe('AlertListItem', () => {
  afterEach(() => {
    cleanup();
  });

  const defaultProps = {
    alert: mockAlert,
    onDelete: vi.fn(),
    onEdit: vi.fn(),
  };

  it('renders alert information correctly', () => {
    render(<AlertListItem {...defaultProps} />);

    expect(screen.getByText('BTC Breakout Alert')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('calls onDelete when delete button is clicked', () => {
    const onDelete = vi.fn();
    render(<AlertListItem {...defaultProps} onDelete={onDelete} />);

    // Find all delete buttons and click the first one
    const deleteButtons = screen.getAllByLabelText('Delete alert');
    expect(deleteButtons.length).toBeGreaterThan(0);
    
    // Use fireEvent directly on the button
    fireEvent.click(deleteButtons[0]);

    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onDelete).toHaveBeenCalledWith(mockAlert);
  });

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = vi.fn();
    render(<AlertListItem {...defaultProps} onEdit={onEdit} />);

    // Find all edit buttons and click the first one
    const editButtons = screen.getAllByLabelText('Edit alert');
    expect(editButtons.length).toBeGreaterThan(0);
    
    // Use fireEvent directly on the button
    fireEvent.click(editButtons[0]);

    expect(onEdit).toHaveBeenCalledTimes(1);
    expect(onEdit).toHaveBeenCalledWith(mockAlert);
  });
});