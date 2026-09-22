import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { alertKindButtonClassName } from '@/lib/alerts/alertKindClassName'
import { CREATE_ALERT_LABELS } from '@/constants/alerts'
import type { NewAlertType } from '@/types/alerts'

type CreateAlertButtonProps = {
  kind: NewAlertType
  onClick: () => void
}

/** Sits in the tab's own toolbar, so the kind is implied by where you clicked. */
export function CreateAlertButton({ kind, onClick }: CreateAlertButtonProps) {
  return (
    <Button
      type="button"
      aria-label={CREATE_ALERT_LABELS[kind]}
      title={CREATE_ALERT_LABELS[kind]}
      className={cn(
        'min-h-11 touch-manipulation sm:min-h-8',
        alertKindButtonClassName(kind),
      )}
      onClick={onClick}
    >
      <Plus data-icon="inline-start" className="h-4 w-4" />
      New
    </Button>
  )
}
