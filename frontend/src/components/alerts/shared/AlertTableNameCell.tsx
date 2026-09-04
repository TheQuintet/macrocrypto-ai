import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

type AlertTableNameCellProps = {
  icon: LucideIcon
  name: string
  secondary?: string
  /** Rendered next to the name, e.g. the macro impact badge. */
  badge?: ReactNode
  /** Wraps the name in a button when the row can be opened. */
  onOpen?: () => void
  openLabel?: string
}

/** Icon chip plus name and supporting line, identical on both alert tables. */
export function AlertTableNameCell({
  icon: Icon,
  name,
  secondary,
  badge,
  onOpen,
  openLabel,
}: AlertTableNameCellProps) {
  return (
    <div className="flex items-center gap-3">
      <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
        <Icon className="size-4" />
      </span>
      <div className="min-w-0">
        <div className="flex min-w-0 items-center gap-2">
          {onOpen ? (
            <button
              type="button"
              aria-label={openLabel}
              onClick={onOpen}
              className="truncate rounded text-sm font-medium hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {name}
            </button>
          ) : (
            <span className="truncate text-sm font-medium">{name}</span>
          )}
          {badge}
        </div>
        {secondary ? (
          <p className="truncate text-xs text-muted-foreground">{secondary}</p>
        ) : null}
      </div>
    </div>
  )
}
