import userEvent from '@testing-library/user-event'
import { act, cleanup, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import {
  expectHistoryOnPage,
  renderSection,
} from './MacroIndicatorsSection.testHelpers'
import { resetPreferencesStore } from '@/stores/preferencesStore.testHelpers'
import { usePreferencesStore } from '@/stores/preferencesStore'

describe('MacroIndicatorsSection', () => {
  beforeEach(() => {
    resetPreferencesStore()
  })

  afterEach(() => {
    cleanup()
    resetPreferencesStore()
  })

  it('shows latest cards and history on the same page', () => {
    renderSection()

    expectHistoryOnPage()
    expect(screen.getByText(/aligned to each btc candle/i)).toHaveTextContent(
      '30d',
    )
  })

  it('follows the shared time range for history', () => {
    renderSection()

    act(() => {
      usePreferencesStore.getState().setTimeRange('90d')
    })

    expectHistoryOnPage()
    expect(screen.getByText(/aligned to each btc candle/i)).toHaveTextContent(
      '90d',
    )
  })

  it('stacks indicator history under BTC price in one panel', () => {
    renderSection()

    const panel = screen.getByRole('region', {
      name: /price and indicator history/i,
    })
    const btc = within(panel).getByRole('heading', { name: 'BTC price' })
    const history = within(panel).getByRole('heading', {
      name: 'Indicator history',
    })

    expect(
      btc.compareDocumentPosition(history) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
  })

  it('puts indicator copy under the history chart', async () => {
    renderSection()

    const chart = await screen.findByRole('img', {
      name: /macro indicator history/i,
    })
    const heading = screen.getByRole('heading', { name: 'Indicator history' })

    expect(
      chart.compareDocumentPosition(heading) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
  })

  it('filters the observations table to one indicator', async () => {
    const user = userEvent.setup()
    renderSection()

    const filter = await screen.findByRole('group', { name: 'Indicator filter' })
    await user.click(within(filter).getByRole('button', { name: 'CPI' }))

    const table = await screen.findByRole('region', {
      name: /historical indicator observations/i,
    })
    expect(within(table).getAllByText(/^cpi$/i).length).toBeGreaterThan(0)
    expect(within(table).queryByText(/gdp/i)).not.toBeInTheDocument()
    expect(
      within(table).queryByText(/federal funds rate/i),
    ).not.toBeInTheDocument()
  })
})
