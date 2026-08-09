import { useState } from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { Bell, Moon, Sun } from 'lucide-react'
import { AppSidebar } from '@/components/AppSidebar'
import { Button } from '@/components/ui/button'
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { navItemFromPathname, routes } from '@/constants/navigation'
import { useTheme } from '@/hooks/useTheme'

/** Shell layout: sidebar + header stay mounted; page content is the route outlet. */
export function AppLayout() {
  const { isDark, toggleTheme } = useTheme()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const { pathname } = useLocation()
  const activeNav = navItemFromPathname(pathname)

  return (
    <TooltipProvider>
      <SidebarProvider open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-14 items-center gap-2 border-b px-4">
            <SidebarTrigger />
            <div className="ml-auto flex items-center gap-2">
              <Button
                type="button"
                variant={activeNav === 'alerts' ? 'secondary' : 'outline'}
                size="icon"
                aria-label="Open alerts"
                asChild
              >
                <Link to={routes.alerts}>
                  <Bell />
                </Link>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="icon"
                aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
                onClick={toggleTheme}
              >
                {isDark ? <Sun /> : <Moon />}
              </Button>
            </div>
          </header>
          <Outlet />
        </SidebarInset>
        <Toaster
          position="bottom-left"
          offset={{
            bottom: '1rem',
            left: sidebarOpen
              ? 'calc(var(--sidebar-width) + 1rem)'
              : 'calc(var(--sidebar-width-icon) + 1rem)',
          }}
          richColors
        />
      </SidebarProvider>
    </TooltipProvider>
  )
}
