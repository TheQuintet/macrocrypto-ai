import { Outlet } from 'react-router-dom'
import { Moon, Sun } from 'lucide-react'
import { NotificationBell } from '@/components/alerts/notifications/NotificationBell'
import { AppSidebar } from '@/components/layout/AppSidebar'
import { AppToaster } from '@/components/layout/AppToaster'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { ALERTS_USER_ID } from '@/constants/alerts'
import { useIsMobile } from '@/hooks/useMobile'
import { useTheme } from '@/hooks/useTheme'

/** Shell layout: sidebar + header stay mounted; page content is the route outlet. */
export function AppLayout() {
  const { isDark, toggleTheme } = useTheme()
  const isMobile = useIsMobile()

  return (
    <TooltipProvider>
      <SidebarProvider defaultOpen={!isMobile}>
        <AppSidebar />
        <SidebarInset className="min-w-0 overflow-x-hidden">
          <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b bg-background/80 px-3 backdrop-blur-sm sm:px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator
              orientation="vertical"
              className="mr-1 hidden data-[orientation=vertical]:h-5 sm:block"
            />
            <span className="min-w-0 truncate font-mono text-sm font-medium tracking-tight">
              MacroCrypto&nbsp;AI
            </span>

            <div className="ml-auto flex shrink-0 items-center gap-1">
              <NotificationBell userId={ALERTS_USER_ID} />
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={
                      isDark ? 'Switch to light theme' : 'Switch to dark theme'
                    }
                    onClick={toggleTheme}
                  >
                    {isDark ? <Sun /> : <Moon />}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  {isDark ? 'Light theme' : 'Dark theme'}
                </TooltipContent>
              </Tooltip>
            </div>
          </header>

          <div className="flex min-w-0 flex-1 flex-col gap-4 p-3 sm:gap-6 sm:p-4 md:p-6 lg:p-8">
            <Outlet />
          </div>
        </SidebarInset>
        <AppToaster />
      </SidebarProvider>
    </TooltipProvider>
  )
}
