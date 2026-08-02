import { useState } from 'react'
import { Bell, Moon, Sun } from 'lucide-react'
import { AppSidebar } from '@/components/app-sidebar'
import { PageContent } from '@/components/page-content'
import { Button } from '@/components/ui/button'
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import type { NavItemId } from '@/constants/navigation'
import { useTheme } from '@/hooks/use-theme'

function App() {
  const { isDark, toggleTheme } = useTheme()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeNav, setActiveNav] = useState<NavItemId>('dashboard')

  return (
    <TooltipProvider>
      <SidebarProvider open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <AppSidebar activeNav={activeNav} onNavigate={setActiveNav} />
        <SidebarInset>
          <header className="flex h-14 items-center gap-2 border-b px-4">
            <SidebarTrigger />
            <div className="ml-auto flex items-center gap-2">
              <Button
                type="button"
                variant={activeNav === 'alerts' ? 'secondary' : 'outline'}
                size="icon"
                aria-label="Open alerts"
                onClick={() => setActiveNav('alerts')}
              >
                <Bell />
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
          <PageContent activeNav={activeNav} />
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

export default App
