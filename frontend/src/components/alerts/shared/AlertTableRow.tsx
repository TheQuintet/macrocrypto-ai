import type { MouseEvent, ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { useAlertListLayout } from './alertListLayout'

type AlertTableRowProps = {
  /** Opens the edit dialog; clicks on buttons inside the row are left alone. */
  onOpen?: () => void
  name: ReactNode
  detail: ReactNode
  repeat: ReactNode
  status: ReactNode
  actions: ReactNode
}

function isInteractiveTarget(event: MouseEvent<HTMLElement>) {
  return Boolean((event.target as HTMLElement).closest('button, a, input, label'))
}

/** Table row from sm up; stacked card below sm so status and delete stay visible. */
export function AlertTableRow({
  onOpen,
  name,
  detail,
  repeat,
  status,
  actions,
}: AlertTableRowProps) {
  const { layout, detailLabel } = useAlertListLayout()

  const handleClick = (event: MouseEvent<HTMLElement>) => {
    if (!onOpen || isInteractiveTarget(event)) return
    onOpen()
  }

  if (layout === 'card') {
    return (
      <article
        data-slot="alert-list-card"
        onClick={handleClick}
        className={cn(
          'rounded-lg border bg-card p-4',
          onOpen && 'cursor-pointer',
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">{name}</div>
          <div className="flex shrink-0 items-center gap-1">
            {status}
            {actions}
          </div>
        </div>
        <div className="mt-3 space-y-2">
          <div>
            <p className="text-xs text-muted-foreground">{detailLabel}</p>
            {detail}
          </div>
          {repeat}
        </div>
      </article>
    )
  }

  return (
    <tr
      onClick={handleClick}
      className={cn(
        'border-b transition-colors last:border-0 hover:bg-muted/30',
        onOpen && 'cursor-pointer',
      )}
    >
      <td className="px-4 py-3">{name}</td>
      <td className="px-4 py-3">{detail}</td>
      <td className="px-4 py-3">
        <div className="flex justify-center">{repeat}</div>
      </td>
      <td className="px-4 py-3">
        <div className="flex justify-center">{status}</div>
      </td>
      <td className="px-4 py-3 text-right">{actions}</td>
    </tr>
  )
}
