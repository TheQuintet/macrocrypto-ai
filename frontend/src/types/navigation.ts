import type { LucideIcon } from 'lucide-react'

export type NavItemId = 'dashboard' | 'macro' | 'forecasts' | 'alerts'

export type PageCopy = {
  title: string
  body?: string
}

export type SidebarNavItem = {
  id: NavItemId
  label: string
  path: string
  icon: LucideIcon
}
