import { describe, expect, it } from 'vitest'
import {
  resolveAlertStatus,
  isAlertEnabled,
  toggledAlertStatus,
  matchesAlertStatusFilter,
} from './alertStatus'

describe('matchesAlertStatusFilter', () => {
  it('keeps every alert when the filter is all', () => {
    expect(matchesAlertStatusFilter('active', 'all')).toBe(true)
    expect(matchesAlertStatusFilter('disabled', 'all')).toBe(true)
  })

  it('keeps enabled alerts when filtering to active', () => {
    expect(matchesAlertStatusFilter('active', 'active')).toBe(true)
    expect(matchesAlertStatusFilter('triggered', 'active')).toBe(true)
    expect(matchesAlertStatusFilter('disabled', 'active')).toBe(false)
  })

  it('keeps paused alerts when filtering to inactive', () => {
    expect(matchesAlertStatusFilter('disabled', 'inactive')).toBe(true)
    expect(matchesAlertStatusFilter('expired', 'inactive')).toBe(true)
    expect(matchesAlertStatusFilter('active', 'inactive')).toBe(false)
  })
})

describe('resolveAlertStatus', () => {
  it('treats inactive as disabled', () => {
    expect(resolveAlertStatus('inactive')).toBe('disabled')
    expect(resolveAlertStatus('INACTIVE')).toBe('disabled')
  })

  it('normalizes casing from the API', () => {
    expect(resolveAlertStatus('DISABLED')).toBe('disabled')
    expect(resolveAlertStatus('Active')).toBe('active')
  })
})

describe('isAlertEnabled', () => {
  it('treats active and triggered as on', () => {
    expect(isAlertEnabled('active')).toBe(true)
    expect(isAlertEnabled('triggered')).toBe(true)
    expect(isAlertEnabled('disabled')).toBe(false)
    expect(isAlertEnabled('expired')).toBe(false)
  })
})

describe('toggledAlertStatus', () => {
  it('pauses an enabled alert and turns an inactive one back on', () => {
    expect(toggledAlertStatus('active')).toBe('disabled')
    expect(toggledAlertStatus('triggered')).toBe('disabled')
    expect(toggledAlertStatus('disabled')).toBe('active')
    expect(toggledAlertStatus('expired')).toBe('active')
  })
})
