import { describe, expect, it } from 'vitest'
import {
  navItemFromPathname,
  pageCopy,
  routes,
  type NavItemId,
} from '@/constants/navigation'

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
})
