import { describe, expect, it } from 'vitest'
import { notificationToastClassName } from '@/lib/alerts/notificationToastClassName'

describe('notificationToastClassName', () => {
  it('uses blue for price alerts', () => {
    expect(notificationToastClassName('price_alert')).toContain('--toast-price-bg')
  })

  it('uses purple for forecast alerts', () => {
    expect(notificationToastClassName('prediction_alert')).toContain(
      '--toast-forecast-bg',
    )
    expect(notificationToastClassName('confidence_alert')).toContain(
      '--toast-forecast-bg',
    )
  })

  it('uses green for macro alerts', () => {
    expect(notificationToastClassName('macro_alert')).toContain('--toast-macro-bg')
  })
})
