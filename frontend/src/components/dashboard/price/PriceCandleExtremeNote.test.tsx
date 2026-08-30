import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { PriceCandleExtremeNote } from '@/components/dashboard/price/PriceCandleExtremeNote'

describe('PriceCandleExtremeNote', () => {
  afterEach(() => {
    cleanup()
  })

  it('marks a high above the open as a green rise', () => {
    render(
      <PriceCandleExtremeNote changePercent={0.625} reference="open" />,
    )

    const note = screen.getByLabelText('↑ +0.63% from open')
    expect(note).toHaveTextContent('↑ +0.63%')
    expect(note).toHaveClass('text-positive')
  })

  it('marks a low below the close as a red drop', () => {
    render(
      <PriceCandleExtremeNote changePercent={-0.3126} reference="close" />,
    )

    const note = screen.getByLabelText('↓ -0.31% from close')
    expect(note).toHaveTextContent('↓ -0.31%')
    expect(note).toHaveClass('text-negative')
  })

  it('mutes a wick that sits on the body', () => {
    render(<PriceCandleExtremeNote changePercent={0} reference="open" />)

    expect(screen.getByLabelText('→ 0.00% from open')).toHaveClass(
      'text-muted-foreground',
    )
  })
})
