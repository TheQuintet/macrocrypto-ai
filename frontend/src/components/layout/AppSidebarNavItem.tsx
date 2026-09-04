import { Link, useLocation } from 'react-router-dom';
import { AppSidebarNavSubItem } from '@/components/layout/AppSidebarNavSubItem';
import {
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
} from '@/components/ui/sidebar';
import { isSidebarNavItemActive } from '@/constants/navigation';
import type { SidebarNavItem } from '@/types/navigation';

type AppSidebarNavItemProps = {
  item: SidebarNavItem;
  onClick?: () => void;
};

export function AppSidebarNavItem({ item, onClick }: AppSidebarNavItemProps) {
  const { pathname } = useLocation();
  const isActive = isSidebarNavItemActive(item.path, pathname);
  const Icon = item.icon;

  const handleClick = () => {
    console.log('[AppSidebarNavItem] Clicked:', item.path);
    onClick?.();
  };

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive} tooltip={item.label}>
        <Link to={item.path} onClick={handleClick}>
          <Icon />
          <span>{item.label}</span>
        </Link>
      </SidebarMenuButton>

      {item.children?.length ? (
        <SidebarMenuSub>
          {item.children.map((child) => (
            <AppSidebarNavSubItem key={child.id} item={child} />
          ))}
        </SidebarMenuSub>
      ) : null}
    </SidebarMenuItem>
  );
}
