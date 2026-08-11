import { useSidebar } from '@/components/ui/sidebar'
import { Toaster } from '@/components/ui/sonner'

/** Toast host positioned relative to the sidebar (desktop) or viewport edge (mobile). */
export function AppToaster() {
  const { open, isMobile } = useSidebar()

  return (
    <Toaster
      position="bottom-left"
      offset={{
        bottom: '1rem',
        left: isMobile
          ? '1rem'
          : open
            ? 'calc(var(--sidebar-width) + 1rem)'
            : 'calc(var(--sidebar-width-icon) + 1rem)',
      }}
      richColors
    />
  )
}
