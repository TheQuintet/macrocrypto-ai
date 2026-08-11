import { describe, expect, it } from 'vitest'
import {
  isSidebarNavItemActive,
  navItemFromPathname,
  pageCopy,
  routes,
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
    expect(navItemFromPathname(routes.alerts)).toBe('alerts')
  })

  it('marks sidebar items active for exact and nested paths', () => {
    expect(isSidebarNavItemActive(routes.dashboard, '/')).toBe(true)
    expect(isSidebarNavItemActive(routes.dashboard, '/macro')).toBe(false)
    expect(isSidebarNavItemActive(routes.macro, '/macro')).toBe(true)
    expect(isSidebarNavItemActive(routes.macro, '/macro/cpi')).toBe(true)
    expect(isSidebarNavItemActive(routes.forecasts, '/macro')).toBe(false)
  })
})
