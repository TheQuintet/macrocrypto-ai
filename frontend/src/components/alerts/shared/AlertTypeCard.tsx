import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

type AlertTypeCardProps = {
  icon: ReactNode
  title: string
  description: string
  onClick: () => void
  className?: string
}

/** One selectable alert kind inside the alert type dialog. */
export function AlertTypeCard({
  icon,
  title,
  description,
  onClick,
  className,
}: AlertTypeCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex flex-col items-center gap-3 rounded-lg border-2 border-border bg-background p-6 text-left transition-all',
        'hover:border-primary/50 hover:shadow-md',
        className,
      )}
    >
      <div className="rounded-full bg-primary/10 p-3 text-primary">{icon}</div>
      <div className="text-center">
        <h3 className="text-sm font-semibold">{title}</h3>
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      </div>
    </button>
  )
}
