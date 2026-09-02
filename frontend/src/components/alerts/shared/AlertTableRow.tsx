import type { MouseEvent, ReactNode } from 'react'
import { cn } from '@/lib/utils'

type AlertTableRowProps = {
  /** Opens the edit dialog; clicks on buttons inside the row are left alone. */
  onOpen?: () => void
  children: ReactNode
}

export function AlertTableRow({ onOpen, children }: AlertTableRowProps) {
  const handleClick = (event: MouseEvent<HTMLTableRowElement>) => {
    if (!onOpen) return
    // Switches, delete buttons and the name button handle their own clicks.
    if ((event.target as HTMLElement).closest('button, a, input, label')) return
    onOpen()
  }

  return (
    <tr
      onClick={handleClick}
      className={cn(
        'border-b transition-colors last:border-0 hover:bg-muted/30',
        onOpen && 'cursor-pointer',
      )}
    >
      {children}
    </tr>
  )
}
