import { describe, expect, it } from 'vitest'
import { mockAlert } from './__tests__/testHelpers'
import { priceAlertDeleteDetails } from './priceAlertDelete'

describe('priceAlertDeleteDetails', () => {
  it('includes name, rule, status, repeat, notify, and note', () => {
    expect(priceAlertDeleteDetails(mockAlert)).toEqual([
      { label: 'Name', value: 'BTC Breakout Alert' },
      { label: 'Rule', value: 'BTC/USD goes above $85,000.00' },
      { label: 'Status', value: 'Active' },
      { label: 'Repeat', value: 'One-time' },
      { label: 'Notify', value: 'In the app' },
      { label: 'Note', value: 'Alert when BTC crosses above 85000' },
    ])
  })

  it('omits name and note when they are empty', () => {
    expect(
      priceAlertDeleteDetails({
        ...mockAlert,
        name: '  ',
        description: null,
        one_time: false,
        notify_in_app: false,
        notify_email: true,
        status: 'disabled',
      }),
    ).toEqual([
      { label: 'Rule', value: 'BTC/USD goes above $85,000.00' },
      { label: 'Status', value: 'Inactive' },
      { label: 'Repeat', value: 'Repeats' },
      { label: 'Notify', value: 'Email' },
    ])
  })

  it('lists both notify channels when both are on', () => {
    const details = priceAlertDeleteDetails({
      ...mockAlert,
      notify_in_app: true,
      notify_email: true,
    })

    expect(details.find((row) => row.label === 'Notify')?.value).toBe(
      'In the app, Email',
    )
  })

  it('shows None when no notify channel is on', () => {
    const details = priceAlertDeleteDetails({
      ...mockAlert,
      notify_in_app: false,
      notify_email: false,
    })

    expect(details.find((row) => row.label === 'Notify')?.value).toBe('None')
  })
})
