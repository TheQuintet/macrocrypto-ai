import { describe, expect, it } from 'vitest'
import {
  isSidebarNavItemActive,
  navItemFromPathname,
  pageCopy,
  routes,
  sidebarNavItems,
} from '@/constants/navigation'
import type { NavItemId } from '@/types/navigation'

const allNavIds = Object.keys(routes) as NavItemId[]

describe('navigation constants', () => {
  it('covers every route id in page copy', () => {
    for (const id of allNavIds) {
      expect(routes[id]).toBeTruthy()
      expect(pageCopy[id].title).toBeTruthy()
    }
  })

  it('resolves pathname to the matching nav id', () => {
    expect(navItemFromPathname('/')).toBe('dashboard')
    expect(navItemFromPathname(routes.macro)).toBe('macro')
    expect(navItemFromPathname(`${routes.forecasts}/x`)).toBe('forecasts')
    // `/macro/calendar` matches both routes; the deeper one wins.
    expect(navItemFromPathname(routes.calendar)).toBe('calendar')
    expect(navItemFromPathname(routes.regimePerformance)).toBe(
      'regimePerformance',
    )
    expect(navItemFromPathname(routes.economicNotifications)).toBe(
      'economicNotifications',
    )
    expect(navItemFromPathname(routes.macro)).toBe('macro')
    expect(navItemFromPathname(routes.alerts)).toBe('alerts')
  })

  it('marks sidebar items active for exact and nested paths', () => {
    expect(isSidebarNavItemActive(routes.dashboard, '/')).toBe(true)
    expect(isSidebarNavItemActive(routes.dashboard, '/macro')).toBe(false)
    expect(isSidebarNavItemActive(routes.macro, '/macro')).toBe(true)
    expect(isSidebarNavItemActive(routes.macro, '/macro/cpi')).toBe(true)
    expect(isSidebarNavItemActive(routes.forecasts, '/macro')).toBe(false)
    expect(isSidebarNavItemActive(routes.alerts, '/alerts')).toBe(true)
    expect(isSidebarNavItemActive(routes.alerts, '/')).toBe(false)
  })

  it('nests regime views, calendar, and notifications under Macro Economy', () => {
    const macro = sidebarNavItems.find((item) => item.id === 'macro')

    expect(macro?.children?.map((child) => child.id)).toEqual([
      'regimePerformance',
      'calendar',
      'economicNotifications',
    ])
    expect(routes.regimePerformance.startsWith(`${routes.macro}/`)).toBe(true)
    expect(routes.calendar.startsWith(`${routes.macro}/`)).toBe(true)
    expect(routes.economicNotifications.startsWith(`${routes.macro}/`)).toBe(
      true,
    )
  })

  it('keeps the macro parent active on its child pages', () => {
    expect(isSidebarNavItemActive(routes.macro, routes.calendar)).toBe(true)
    expect(
      isSidebarNavItemActive(routes.macro, routes.regimePerformance),
    ).toBe(true)
    expect(
      isSidebarNavItemActive(routes.macro, routes.economicNotifications),
    ).toBe(true)
    expect(isSidebarNavItemActive(routes.calendar, routes.calendar)).toBe(true)
    expect(
      isSidebarNavItemActive(routes.regimePerformance, routes.regimePerformance),
    ).toBe(true)
    expect(isSidebarNavItemActive(routes.calendar, routes.macro)).toBe(false)
    expect(
      isSidebarNavItemActive(routes.regimePerformance, routes.macro),
    ).toBe(false)
    expect(
      isSidebarNavItemActive(routes.economicNotifications, routes.macro),
    ).toBe(false)
  })

  it('lists Alerts in the sidebar next to the other pages', () => {
    expect(sidebarNavItems.map((item) => item.id)).toEqual([
      'dashboard',
      'macro',
      'forecasts',
      'alerts',
    ])
  })
})
