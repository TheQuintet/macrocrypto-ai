import { useEffect, useState, type CSSProperties } from 'react'
import {
  CircleCheckIcon,
  InfoIcon,
  Loader2Icon,
  OctagonXIcon,
  TriangleAlertIcon,
} from 'lucide-react'
import { Toaster as Sonner, type ToasterProps } from 'sonner'
import { listenForToastClosePointer } from '@/lib/toastClosePointer'

function useDocumentTheme(): NonNullable<ToasterProps['theme']> {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const root = document.documentElement

    const syncTheme = () => {
      setTheme(root.classList.contains('dark') ? 'dark' : 'light')
    }

    syncTheme()

    const observer = new MutationObserver(syncTheme)
    observer.observe(root, { attributes: true, attributeFilter: ['class'] })

    return () => observer.disconnect()
  }, [])

  return theme
}

const Toaster = ({ ...props }: ToasterProps) => {
  const theme = useDocumentTheme()

  useEffect(() => listenForToastClosePointer(), [])

  return (
    <Sonner
      theme={theme}
      className="toaster group"
      icons={{
        success: <CircleCheckIcon className="size-4" />,
        info: <InfoIcon className="size-4" />,
        warning: <TriangleAlertIcon className="size-4" />,
        error: <OctagonXIcon className="size-4" />,
        loading: <Loader2Icon className="size-4 animate-spin" />,
      }}
      style={
        {
          '--normal-bg': 'var(--popover)',
          '--normal-text': 'var(--popover-foreground)',
          '--normal-border': 'var(--border)',
          '--border-radius': 'var(--radius)',
          '--success-bg': 'var(--toast-success-bg)',
          '--success-text': 'var(--toast-success-text)',
          '--success-border': 'var(--toast-success-bg)',
          '--error-bg': 'var(--toast-error-bg)',
          '--error-text': 'var(--toast-error-text)',
          '--error-border': 'var(--toast-error-bg)',
          '--warning-bg': 'var(--toast-warning-bg)',
          '--warning-text': 'var(--toast-warning-text)',
          '--warning-border': 'var(--toast-warning-bg)',
          '--info-bg': 'var(--toast-info-bg)',
          '--info-text': 'var(--toast-info-text)',
          '--info-border': 'var(--toast-info-bg)',
          '--toast-close-button-start': 'unset',
          '--toast-close-button-end': '0',
          '--toast-close-button-transform': 'translate(35%, -35%)',
        } as CSSProperties
      }
      toastOptions={{
        classNames: {
          toast:
            'cn-toast relative !shadow-lg !border-transparent [&_[data-title]]:!font-semibold [&_[data-description]]:!opacity-95 [&_[data-description]]:whitespace-pre-line',
          closeButton:
            '!z-50 !size-6 !pointer-events-auto !bg-background !text-foreground !border-border hover:!bg-muted [&_svg]:pointer-events-none',
          success:
            '!bg-[var(--toast-success-bg)] !text-[var(--toast-success-text)] [&_[data-icon]]:!text-[var(--toast-success-text)]',
          error:
            '!bg-[var(--toast-error-bg)] !text-[var(--toast-error-text)] [&_[data-icon]]:!text-[var(--toast-error-text)]',
          warning:
            '!bg-[var(--toast-warning-bg)] !text-[var(--toast-warning-text)] [&_[data-icon]]:!text-[var(--toast-warning-text)]',
          info: '!bg-[var(--toast-info-bg)] !text-[var(--toast-info-text)] [&_[data-icon]]:!text-[var(--toast-info-text)]',
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
