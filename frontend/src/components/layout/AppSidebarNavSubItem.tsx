import { Link, useLocation } from 'react-router-dom'
import {
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from '@/components/ui/sidebar'
import { isSidebarNavItemActive } from '@/constants/navigation'
import type { SidebarNavItem } from '@/types/navigation'

type AppSidebarNavSubItemProps = {
  item: SidebarNavItem
}

/** A nested navigation link, e.g. the calendar under macro indicators. */
export function AppSidebarNavSubItem({ item }: AppSidebarNavSubItemProps) {
  const { pathname } = useLocation()
  const isActive = isSidebarNavItemActive(item.path, pathname)
  const Icon = item.icon

  return (
    <SidebarMenuSubItem>
      <SidebarMenuSubButton asChild isActive={isActive}>
        <Link to={item.path}>
          <Icon />
          <span>{item.label}</span>
        </Link>
      </SidebarMenuSubButton>
    </SidebarMenuSubItem>
  )
}
