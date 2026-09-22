import { fireEvent, screen, waitFor } from '@testing-library/react';
import type { UserEvent } from '@testing-library/user-event';
import { expect } from 'vitest';
import { MacroAlertHistory } from '@/components/alerts/macro/MacroAlertHistory';
import { renderWithQuery } from '@/test/renderWithQuery';

/** The simulated feed resolves on a timer, and the first render in a file is slow. */
const FIND_TIMEOUT_MS = 5000;

/**
 * With no alert API base URL configured (vitest pins them empty) the view runs
 * on its simulated history, which is anchored to the current date.
 */
export function renderMacroAlertHistory() {
  return renderWithQuery(<MacroAlertHistory userId="user-1" />);
}

export function findTable() {
  return screen.findByRole('table', undefined, {
    timeout: FIND_TIMEOUT_MS,
  });
}

/** The event name in each body row, in the order they are rendered. */
export async function listedAlertNames(): Promise<string[]> {
  await findTable();

  return screen
    .getAllByRole('row')
    .slice(1)
    .map((row) => row.querySelector('td')?.textContent ?? '');
}

export async function chooseEventType(user: UserEvent, value: string) {
  await findTable();
  await user.selectOptions(
    screen.getByRole('combobox', { name: 'Event type filter' }),
    value,
  );
}

export async function searchAlerts(user: UserEvent, query: string) {
  await findTable();
  const box = screen.getByPlaceholderText('Search sent alerts...');
  await user.clear(box);
  if (query) {
    await user.type(box, query);
  }
}

/** Native date inputs are set directly; jsdom does not model typed segments. */
export function setSentRange(start: string, end: string) {
  if (start) {
    fireEvent.change(screen.getByLabelText('From'), {
      target: { value: start },
    });
  }
  if (end) {
    fireEvent.change(screen.getByLabelText('To'), { target: { value: end } });
  }
}

export async function expectMessage(text: string | RegExp) {
  await waitFor(
    () => {
      expect(screen.getByText(text)).toBeInTheDocument();
    },
    { timeout: FIND_TIMEOUT_MS },
  );
}

export function getExportButton() {
  return screen.getByRole('button', { name: /export/i });
}

export function queryPagination() {
  return screen.queryByRole('navigation');
}
