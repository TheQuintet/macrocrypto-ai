import {
  ChartLine,
  LayoutDashboard,
  Landmark,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export type NavItemId = 'dashboard' | 'macro' | 'forecasts' | 'alerts'

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

export const sidebarNavItems: {
  id: Exclude<NavItemId, 'alerts'>
  label: string
  icon: LucideIcon
}[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
  },
  {
    id: 'macro',
    label: 'Macro indicators',
    icon: Landmark,
  },
  {
    id: 'forecasts',
    label: 'Forecasts',
    icon: ChartLine,
  },
]
