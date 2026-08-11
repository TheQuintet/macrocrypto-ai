import {
  ChartLine,
  LayoutDashboard,
  Landmark,
} from 'lucide-react'
import type {
  NavItemId,
  PageCopy,
  SidebarNavItem,
} from '@/types/navigation'

/** Absolute app paths — use for Link, Navigate, and Route. */
export const routes = {
  dashboard: '/',
  macro: '/macro',
  forecasts: '/forecasts',
  alerts: '/alerts',
} as const satisfies Record<NavItemId, string>

export const pageCopy: Record<NavItemId, PageCopy> = {
  dashboard: {
    title: 'Dashboard',
    body: 'Live Bitcoin price with the macro context driving it — chart, regime, and key indicators at a glance.',
  },
  macro: {
    title: 'Macro indicators',
    body: 'The macroeconomic backdrop behind Bitcoin — inflation, policy rates, and growth in one view.',
  },
  forecasts: {
    title: 'Forecasts',
    body: "The model's 24-hour Bitcoin outlook, with a confidence read on the current signal.",
  },
  alerts: {
    title: 'Alerts',
    body: 'Create rules to get notified when price or macro conditions cross your thresholds.',
  },
}

export const sidebarNavItems: SidebarNavItem[] = [
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

/** Whether a sidebar nav item matches the current pathname. */
export function isSidebarNavItemActive(
  itemPath: string,
  pathname: string,
): boolean {
  if (itemPath === routes.dashboard) {
    return pathname === routes.dashboard
  }

  return pathname === itemPath || pathname.startsWith(`${itemPath}/`)
}
