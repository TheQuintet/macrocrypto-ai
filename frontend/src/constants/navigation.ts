import {
  AlarmClock,
  Bell,
  CalendarDays,
  ChartLine,
  LayoutDashboard,
  Landmark,
} from 'lucide-react';
import type { NavItemId, PageCopy, SidebarNavItem } from '@/types/navigation';

/** Absolute app paths — use for Link, Navigate, and Route. */
export const routes = {
  dashboard: '/',
  macro: '/macro',
  calendar: '/macro/calendar',
  economicNotifications: '/macro/notifications',
  forecasts: '/forecasts',
  alerts: '/alerts',
} as const satisfies Record<NavItemId, string>;

export const pageCopy: Record<NavItemId, PageCopy> = {
  dashboard: {
    title: 'Dashboard',
    body: 'Live Bitcoin price with the macro context driving it — chart, regime, and key indicators at a glance.',
  },
  macro: {
    title: 'Macro indicators',
    body: 'The macroeconomic backdrop behind Bitcoin — inflation, policy rates, and growth in one view.',
  },
  calendar: {
    title: 'Economic calendar',
    body: 'Scheduled macro releases and the alerts you have on them — Fed decisions, CPI, jobs, and GDP.',
  },
  economicNotifications: {
    title: 'Economic notifications',
    body: 'Macro alerts that were actually sent — search, filter, and export the history.',
  },
  forecasts: {
    title: 'Forecasts',
    body: "The model's 24-hour Bitcoin outlook, with a confidence read on the current signal.",
  },
  alerts: {
    title: 'Alerts',
  },
};

export const sidebarNavItems: SidebarNavItem[] = [
  {
    id: 'dashboard',
    label: pageCopy.dashboard.title,
    path: routes.dashboard,
    icon: LayoutDashboard,
  },
  {
    id: 'macro',
    label: pageCopy.macro.title,
    path: routes.macro,
    icon: Landmark,
    children: [
      {
        id: 'calendar',
        label: pageCopy.calendar.title,
        path: routes.calendar,
        icon: CalendarDays,
      },
      {
        id: 'economicNotifications',
        label: pageCopy.economicNotifications.title,
        path: routes.economicNotifications,
        icon: Bell,
      },
    ],
  },
  {
    id: 'forecasts',
    label: pageCopy.forecasts.title,
    path: routes.forecasts,
    icon: ChartLine,
  },
  {
    id: 'alerts',
    label: pageCopy.alerts.title,
    path: routes.alerts,
    icon: AlarmClock,
  },
];

/** Resolve the active nav item from the current pathname. */
export function navItemFromPathname(pathname: string): NavItemId {
  const matches = (Object.keys(routes) as NavItemId[]).filter((id) => {
    if (id === 'dashboard') return false;
    const path = routes[id];
    return pathname === path || pathname.startsWith(`${path}/`);
  });

  // `/macro/calendar` and `/macro/notifications` also match `macro` — the
  // deeper route is the one the reader is actually on.
  const match = matches.sort((a, b) => routes[b].length - routes[a].length)[0];

  return match ?? 'dashboard';
}

/** Whether a sidebar nav item matches the current pathname. */
export function isSidebarNavItemActive(
  itemPath: string,
  pathname: string,
): boolean {
  if (itemPath === routes.dashboard) {
    return pathname === routes.dashboard;
  }

  return pathname === itemPath || pathname.startsWith(`${itemPath}/`);
}
