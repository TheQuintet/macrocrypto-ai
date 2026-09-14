import { cleanup, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it } from 'vitest';
import {
  chooseEventType,
  expectMessage,
  getExportButton,
  listedAlertNames,
  queryPagination,
  renderMacroAlertHistory,
  searchAlerts,
  setSentRange,
} from './MacroAlertHistory.testHelpers';

describe('MacroAlertHistory', () => {
  afterEach(() => {
    cleanup();
  });

  it('lists the alerts that were sent, most recent first', async () => {
    renderMacroAlertHistory();

    const names = await listedAlertNames();

    expect(names[0]).toBe('FOMC rate decision');
    expect(names).toContain('CPI release');
  });

  it('spells out how far ahead of the event each alert went', async () => {
    renderMacroAlertHistory();
    await listedAlertNames();

    expect(screen.getAllByText('12 hours before').length).toBeGreaterThan(0);
    expect(screen.getAllByText('1 day before').length).toBeGreaterThan(0);
  });

  it('filters by event type', async () => {
    const user = userEvent.setup();
    renderMacroAlertHistory();

    await chooseEventType(user, 'fed');

    const names = await listedAlertNames();
    expect(names.length).toBeGreaterThan(0);
    expect(
      names.every(
        (name) => name.includes('FOMC') || name.includes('Federal'),
      ),
    ).toBe(true);
  });

  it('filters by search across the loaded history', async () => {
    const user = userEvent.setup();
    renderMacroAlertHistory();

    await searchAlerts(user, 'payrolls');

    // The seed sends the same release more than once, so a search narrows to
    // every matching alert rather than to a single row.
    const names = await listedAlertNames();
    expect(names.length).toBeGreaterThan(0);
    expect(names.every((name) => name === 'Non-farm payrolls')).toBe(true);
  });

  it('distinguishes no matches from no history', async () => {
    const user = userEvent.setup();
    renderMacroAlertHistory();

    await searchAlerts(user, 'no such alert');

    await expectMessage('No sent alerts match these filters.');
  });

  it('filters by the date the alert was sent', async () => {
    const user = userEvent.setup();
    renderMacroAlertHistory();
    await searchAlerts(user, '');

    // The seed spans the last ~80 days, so a window far in the past is empty.
    setSentRange('2020-01-01', '2020-01-31');

    await expectMessage('No sent alerts match these filters.');
  });

  it('paginates a history longer than one page', async () => {
    renderMacroAlertHistory();

    expect(await listedAlertNames()).toHaveLength(10);
    expect(queryPagination()).toBeInTheDocument();
  });

  it('offers an export, disabled when there is nothing to export', async () => {
    const user = userEvent.setup();
    renderMacroAlertHistory();
    await listedAlertNames();

    expect(getExportButton()).toBeEnabled();

    await searchAlerts(user, 'no such alert');

    expect(getExportButton()).toBeDisabled();
  });
});
