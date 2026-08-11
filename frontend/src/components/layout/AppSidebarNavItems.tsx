import { AppSidebarNavItem } from '@/components/layout/AppSidebarNavItem'
import { SidebarMenu } from '@/components/ui/sidebar'
import { sidebarNavItems } from '@/constants/navigation'

/** Renders the primary sidebar navigation links. */
export function AppSidebarNavItems() {
  return (
    <SidebarMenu>
      {sidebarNavItems.map((item) => (
        <AppSidebarNavItem key={item.id} item={item} />
      ))}
    </SidebarMenu>
  )
}
