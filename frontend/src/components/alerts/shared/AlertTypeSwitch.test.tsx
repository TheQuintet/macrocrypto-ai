import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AlertTypeSwitch } from './AlertTypeSwitch'

describe('AlertTypeSwitch', () => {
  it('paints each icon with its alert-kind color', () => {
    render(<AlertTypeSwitch value="price" onChange={vi.fn()} />)

    expect(screen.getByRole('button', { name: 'Price alert' }).className).toContain(
      '--toast-price-bg',
    )
    expect(screen.getByRole('button', { name: 'Macro event alert' }).className).toContain(
      '--toast-macro-bg',
    )
    expect(screen.getByRole('button', { name: 'Prediction alert' }).className).toContain(
      '--toast-forecast-bg',
    )
  })
})
