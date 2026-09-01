import { AppSidebarNavItem } from '@/components/layout/AppSidebarNavItem';
import { SidebarMenu } from '@/components/ui/sidebar';
import { sidebarNavItems } from '@/constants/navigation';

interface AppSidebarNavItemsProps {
  onNavigate?: (path: string) => void;
}

/** Renders the primary sidebar navigation links. */
export function AppSidebarNavItems({ onNavigate }: AppSidebarNavItemsProps) {
  console.log('[AppSidebarNavItems] Received onNavigate:', !!onNavigate);

  const handleItemClick = (path: string) => {
    console.log('[AppSidebarNavItems] Item clicked, calling onNavigate for:', path);
    onNavigate?.(path);
  };

  return (
    <SidebarMenu>
      {sidebarNavItems.map((item) => (
        <AppSidebarNavItem
          key={item.id}
          item={item}
          onClick={() => handleItemClick(item.path)}
        />
      ))}
    </SidebarMenu>
  );
}