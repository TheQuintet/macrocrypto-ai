import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { AlertTypeSelector } from './AlertTypeSelector'

function renderSelector(overrides: { open?: boolean } = {}) {
  const onSelect = vi.fn()
  const onOpenChange = vi.fn()

  render(
    <AlertTypeSelector
      open={overrides.open ?? true}
      onOpenChange={onOpenChange}
      onSelect={onSelect}
    />,
  )

  return { onSelect, onOpenChange }
}

describe('AlertTypeSelector', () => {
  afterEach(() => {
    cleanup()
  })

  it('offers price and macro event alerts', () => {
    renderSelector()

    expect(screen.getByText('Choose alert type')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Price alert/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Macro event alert/ })).toBeInTheDocument()
  })

  it('reports the chosen type and closes', async () => {
    const user = userEvent.setup()
    const { onSelect, onOpenChange } = renderSelector()

    await user.click(screen.getByRole('button', { name: /Macro event alert/ }))

    expect(onSelect).toHaveBeenCalledWith('macro')
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('renders nothing when closed', () => {
    renderSelector({ open: false })

    expect(screen.queryByText('Choose alert type')).not.toBeInTheDocument()
  })
})
