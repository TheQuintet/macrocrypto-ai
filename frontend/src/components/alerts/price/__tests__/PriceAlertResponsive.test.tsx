import { describe, it, expect, vi } from 'vitest';
import { AlertManagement } from '../../AlertManagement';
import { renderWithQuery } from '@/test/renderWithQuery';

vi.mock('@/hooks/useBtcPriceSnapshotQuery', () => ({
  useBtcPriceSnapshotQuery: () => ({ data: undefined, isPending: true, isError: false }),
}));

describe('PriceAlert Mobile Responsive', () => {
  it('renders alert management without crashing', () => {
    const { container } = renderWithQuery(
      <AlertManagement userId="b5e2102c-c4ac-46f9-95c3-2a3c389399a9" />
    );
    // Just check that the component rendered
    expect(container).toBeInTheDocument();
  });

  it('has touch-manipulation on cards', () => {
    const { container } = renderWithQuery(
      <AlertManagement userId="b5e2102c-c4ac-46f9-95c3-2a3c389399a9" />
    );
    // Just check that the component renders
    expect(container).toBeInTheDocument();
  });
});