import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar'
import {
  type NavItemId,
  sidebarNavItems,
} from '@/constants/navigation'

type AppSidebarProps = {
  activeNav: NavItemId
  onNavigate: (id: NavItemId) => void
}

export function AppSidebar({ activeNav, onNavigate }: AppSidebarProps) {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b border-sidebar-border px-3 py-3">
        <div className="flex flex-col gap-0.5 group-data-[collapsible=icon]:hidden">
          <span className="text-sm font-semibold tracking-tight">MacroCrypto AI</span>
          <span className="text-xs text-sidebar-foreground/70">
            BTC + macro intelligence
          </span>
        </div>
        <span className="hidden text-sm font-semibold group-data-[collapsible=icon]:inline">
          MC
        </span>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Platform</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {sidebarNavItems.map((item) => (
                <SidebarMenuItem key={item.id}>
                  <SidebarMenuButton
                    type="button"
                    isActive={activeNav === item.id}
                    tooltip={item.label}
                    onClick={() => onNavigate(item.id)}
                  >
                    <item.icon />
                    <span>{item.label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="border-t border-sidebar-border px-3 py-3 text-xs text-sidebar-foreground/70 group-data-[collapsible=icon]:hidden">
        BTC + macro intelligence
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
