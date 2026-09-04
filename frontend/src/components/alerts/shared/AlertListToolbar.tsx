import type { ReactNode } from 'react'

type AlertListToolbarProps = {
  summary: string
  children: ReactNode
}

/** Count on the left, filters and actions on the right — same on both tabs. */
export function AlertListToolbar({ summary, children }: AlertListToolbarProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-muted-foreground">{summary}</p>
      <div className="flex flex-wrap items-center gap-2">{children}</div>
    </div>
  )
}
