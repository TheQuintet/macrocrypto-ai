import { isValidElement } from 'react'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { toast } from 'sonner'
import { showToast, NOTIFICATION_TOAST_DURATION_MS } from './ToastNotification'

vi.mock('sonner', () => {
  const toastFn = Object.assign(vi.fn(() => 'toast-1'), {
    success: vi.fn(() => 'toast-1'),
    error: vi.fn(() => 'toast-1'),
    info: vi.fn(() => 'toast-1'),
    warning: vi.fn(() => 'toast-1'),
    dismiss: vi.fn(),
  })
  return { toast: toastFn }
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('showToast', () => {
  it('leaves placement to AppToaster instead of pinning top-right', () => {
    showToast.success('Alert created successfully')
    showToast.info('Refreshing alerts...')

    const successOptions = vi.mocked(toast.success).mock.calls[0]?.[1]
    const infoOptions = vi.mocked(toast.info).mock.calls[0]?.[1]

    expect(successOptions).not.toHaveProperty('position')
    expect(infoOptions).not.toHaveProperty('position')
  })

  it('opens from a click on the toast and then dismisses it', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    showToast.info('BTC broke $72,000', 'Price alert', 10_000, { onClick })

    const infoOptions = vi.mocked(toast.info).mock.calls[0]?.[1]
    expect(infoOptions).toMatchObject({
      duration: 10_000,
      className: 'cursor-pointer',
    })

    const action = infoOptions?.action
    expect(isValidElement(action)).toBe(true)
    if (!isValidElement<{ className?: string }>(action)) return
    expect(action.props.className).toContain('right-8')

    render(action)
    await user.click(screen.getByRole('button', { name: 'Open BTC broke $72,000' }))

    expect(onClick).toHaveBeenCalledTimes(1)
    expect(toast.dismiss).toHaveBeenCalledWith('toast-1')
  })

  it('dismisses every toast at once', () => {
    showToast.dismissAll()

    expect(toast.dismiss).toHaveBeenCalledWith()
  })

  it('dismisses a single toast by id', () => {
    showToast.dismiss('n-breakout')

    expect(toast.dismiss).toHaveBeenCalledWith('n-breakout')
  })

  it('keeps a notification toast visible for two minutes', () => {
    showToast.notification('BTC broke $72,000', 'Price alert', {
      notificationType: 'price_alert',
    })

    expect(toast).toHaveBeenCalledWith(
      'BTC broke $72,000',
      expect.objectContaining({
        duration: NOTIFICATION_TOAST_DURATION_MS,
      }),
    )
  })

  it('tags a notification toast with a stable id', () => {
    showToast.notification('BTC broke $72,000', 'Price alert', {
      id: 'n-breakout',
      notificationType: 'price_alert',
    })

    expect(toast).toHaveBeenCalledWith(
      'BTC broke $72,000',
      expect.objectContaining({
        id: 'n-breakout',
      }),
    )
  })

  it('colors a price notification toast blue', () => {
    showToast.notification('BTC broke $72,000', 'Price alert', {
      notificationType: 'price_alert',
    })

    expect(toast).toHaveBeenCalledWith(
      'BTC broke $72,000',
      expect.objectContaining({
        className: expect.stringContaining('--toast-price-bg'),
        duration: NOTIFICATION_TOAST_DURATION_MS,
      }),
    )
  })

  it('colors a forecast notification toast purple', () => {
    showToast.notification('24h outlook turned bullish', 'Forecast alert', {
      notificationType: 'prediction_alert',
    })

    expect(toast).toHaveBeenCalledWith(
      '24h outlook turned bullish',
      expect.objectContaining({
        className: expect.stringContaining('--toast-forecast-bg'),
      }),
    )
  })

  it('colors a macro notification toast green', () => {
    showToast.notification('NFP beat expectations', 'Macro alert', {
      notificationType: 'macro_alert',
    })

    expect(toast).toHaveBeenCalledWith(
      'NFP beat expectations',
      expect.objectContaining({
        className: expect.stringContaining('--toast-macro-bg'),
      }),
    )
  })
})
