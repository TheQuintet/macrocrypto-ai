import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { AlertStatusBadge } from './AlertStatusBadge'

afterEach(() => {
  cleanup()
})

describe('AlertStatusBadge', () => {
  it('shows Inactive for a disabled alert', () => {
    render(<AlertStatusBadge status="disabled" />)
    expect(screen.getByText('Inactive')).toBeInTheDocument()
    expect(screen.queryByText('Active')).not.toBeInTheDocument()
  })

  it('shows Active for an active alert', () => {
    render(<AlertStatusBadge status="active" />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })
})
