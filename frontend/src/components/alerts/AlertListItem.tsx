import { Bell, Trash2 } from 'lucide-react'
import type { DraftAlert } from '@/types/alerts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

type AlertListItemProps = {
  alert: DraftAlert
  onDelete: (id: string) => void
}

/** Single alert row content (rule, status, delete). */
export function AlertListItem({ alert, onDelete }: AlertListItemProps) {
  return (
    <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:gap-4">
      <div className="flex min-w-0 flex-1 items-start gap-3 sm:items-center sm:gap-4">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
          <Bell className="size-4" />
        </span>
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <span className="truncate text-sm font-medium">{alert.rule}</span>
          <span className="truncate text-xs text-muted-foreground">
            {alert.detail}
          </span>
        </div>
      </div>
      <div className="flex items-center justify-between gap-2 sm:justify-end">
        <Badge variant="secondary">Draft</Badge>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label="Delete alert"
          onClick={() => onDelete(alert.id)}
        >
          <Trash2 />
        </Button>
      </div>
    </div>
  )
}
