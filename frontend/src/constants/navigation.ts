import {
  ChartLine,
  LayoutDashboard,
  Landmark,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

/** Absolute app paths — use for Link, Navigate, and Route. */
export const routes = {
  dashboard: '/',
  macro: '/macro',
  forecasts: '/forecasts',
  alerts: '/alerts',
} as const

export type NavItemId = keyof typeof routes

export const pageCopy: Record<
  NavItemId,
  {
    title: string
    body: string
  }
> = {
  dashboard: {
    title: 'Dashboard',
    body: 'Live BTC price monitoring with macroeconomic context.',
  },
  macro: {
    title: 'Macro indicators',
    body: 'Track inflation (CPI), interest rates, and GDP in one view.',
  },
  forecasts: {
    title: 'Forecasts',
    body: 'AI-powered 24h BTC predictions with confidence context.',
  },
  alerts: {
    title: 'Alerts',
    body: 'Manage price and macro trigger notifications.',
  },
}

type SidebarNavItemId = Exclude<NavItemId, 'alerts'>

export const sidebarNavItems: {
  id: SidebarNavItemId
  label: string
  path: string
  icon: LucideIcon
}[] = [
  {
    id: 'dashboard',
    label: pageCopy.dashboard.title,
    path: routes.dashboard,
    icon: LayoutDashboard,
  },
  {
    id: 'macro',
    label: pageCopy.macro.title,
    path: routes.macro,
    icon: Landmark,
  },
  {
    id: 'forecasts',
    label: pageCopy.forecasts.title,
    path: routes.forecasts,
    icon: ChartLine,
  },
]

/** Resolve the active nav item from the current pathname. */
export function navItemFromPathname(pathname: string): NavItemId {
  const match = (Object.keys(routes) as NavItemId[]).find((id) => {
    if (id === 'dashboard') return false
    const path = routes[id]
    return pathname === path || pathname.startsWith(`${path}/`)
  })
  return match ?? 'dashboard'
}
