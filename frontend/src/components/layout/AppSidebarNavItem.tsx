import { Link, useLocation } from 'react-router-dom'
import {
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar'
import { isSidebarNavItemActive } from '@/constants/navigation'
import type { SidebarNavItem } from '@/types/navigation'

type AppSidebarNavItemProps = {
  item: SidebarNavItem
}

export function AppSidebarNavItem({ item }: AppSidebarNavItemProps) {
  const { pathname } = useLocation()
  const isActive = isSidebarNavItemActive(item.path, pathname)
  const Icon = item.icon

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive} tooltip={item.label}>
        <Link to={item.path}>
          <Icon />
          <span>{item.label}</span>
        </Link>
      </SidebarMenuButton>
    </SidebarMenuItem>
  )
}
