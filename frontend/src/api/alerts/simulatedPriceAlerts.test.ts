import { afterEach, describe, expect, it } from 'vitest'
import {
  buildSimulatedPriceAlerts,
  resetSimulatedPriceAlerts,
  simulatedAlertIds,
  simulateCreateAlert,
  simulateDeleteAlert,
  simulateGetAlert,
  simulateGetAlerts,
  simulateUpdateAlert,
} from '@/api/alerts/simulatedPriceAlerts'
import { ALERTS_USER_ID } from '@/constants/alerts'

afterEach(() => {
  resetSimulatedPriceAlerts()
})

describe('buildSimulatedPriceAlerts', () => {
  it('seeds active and inactive BTC alerts for the demo user', () => {
    const alerts = buildSimulatedPriceAlerts()

    expect(alerts.length).toBeGreaterThan(0)
    expect(alerts.every((alert) => alert.user_id === ALERTS_USER_ID)).toBe(true)
    expect(alerts.some((alert) => alert.status === 'active')).toBe(true)
    expect(alerts.some((alert) => alert.status === 'disabled')).toBe(true)
    expect(alerts.some((alert) => alert.name)).toBe(true)
    expect(alerts.some((alert) => !alert.name)).toBe(true)
  })
})

describe('simulateGetAlerts', () => {
  it('returns the seed list for the demo user', async () => {
    const response = await simulateGetAlerts(ALERTS_USER_ID)

    expect(response.total).toBe(buildSimulatedPriceAlerts().length)
    expect(response.alerts[0]?.id).toBe(simulatedAlertIds.breakout)
  })

  it('returns nothing for a different user', async () => {
    const response = await simulateGetAlerts('someone-else')

    expect(response.alerts).toEqual([])
    expect(response.total).toBe(0)
  })
})

describe('simulate price alert writes', () => {
  it('creates, updates, and deletes in memory', async () => {
    const created = await simulateCreateAlert({
      user_id: ALERTS_USER_ID,
      threshold_price: 72_500,
      alert_type: 'reaches',
      name: 'New watch',
    })

    expect(created.status).toBe('active')
    expect(await simulateGetAlert(created.id)).toMatchObject({
      name: 'New watch',
      threshold_price: 72_500,
    })

    const updated = await simulateUpdateAlert(created.id, { status: 'disabled' })
    expect(updated.status).toBe('disabled')

    await simulateDeleteAlert(created.id)
    await expect(simulateGetAlert(created.id)).rejects.toThrow(/not found/)
  })
})
