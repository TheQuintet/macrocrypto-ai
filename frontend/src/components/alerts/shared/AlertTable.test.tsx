import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { renderAlertTable, renderEmptyAlertTable } from './AlertTable.testHelpers'

describe('AlertTable', () => {
  it('keeps the table for sm+ and stacks cards below that', () => {
    renderAlertTable()

    expect(document.querySelector('[data-slot="alert-list-cards"]')).toHaveClass('sm:hidden')
    expect(document.querySelector('[data-slot="alert-list-table"]')).toHaveClass('hidden', 'sm:block')
    expect(screen.getAllByText('Breakout')).toHaveLength(2)
    expect(screen.getByRole('columnheader', { name: 'Alert' })).toBeInTheDocument()
  })

  it('renders the empty message in both layouts', () => {
    renderEmptyAlertTable()

    expect(screen.getAllByText('No alerts found matching your filters')).toHaveLength(2)
  })
})
