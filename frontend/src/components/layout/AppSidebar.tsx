import { Link } from 'react-router-dom';
import { AppSidebarNavItems } from '@/components/layout/AppSidebarNavItems';
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
} from '@/components/ui/sidebar';
import { routes } from '@/constants/navigation';

interface AppSidebarProps {
  onNavigate?: (path: string) => void;
}

export function AppSidebar({ onNavigate }: AppSidebarProps) {
  console.log('[AppSidebar] Received onNavigate:', !!onNavigate);

  const handleLogoClick = () => {
    console.log('[AppSidebar] Logo clicked');
    onNavigate?.(routes.dashboard);
  };

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link to={routes.dashboard} onClick={handleLogoClick}>
                <span className="flex aspect-square size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
                  <span className="font-mono text-sm font-semibold">MAI</span>
                </span>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold">MacroCrypto AI</span>
                  <span className="text-xs text-muted-foreground">
                    Bitcoin intelligence
                  </span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <AppSidebarNavItems onNavigate={onNavigate} />
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="border-t border-sidebar-border px-3 py-3 text-xs text-sidebar-foreground/70 group-data-[collapsible=icon]:hidden">
        BTC + macro intelligence
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
