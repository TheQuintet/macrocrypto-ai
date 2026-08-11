import type { LucideIcon } from 'lucide-react'

export type NavItemId = 'dashboard' | 'macro' | 'forecasts' | 'alerts'

export type SidebarNavItemId = Exclude<NavItemId, 'alerts'>

export type PageCopy = {
  title: string
  body: string
}

export type SidebarNavItem = {
  id: SidebarNavItemId
  label: string
  path: string
  icon: LucideIcon
}
