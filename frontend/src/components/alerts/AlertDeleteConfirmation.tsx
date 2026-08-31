import { ConfirmationDialog } from '@/components/alerts/shared/ConfirmationDialog'
import { priceAlertDeleteDetails } from '@/components/alerts/price/priceAlertDelete'
import type { PriceAlert } from '@/types/alerts/priceAlert'

type AlertDeleteConfirmationProps = {
  alert: PriceAlert | null
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
  isLoading?: boolean
}

export function AlertDeleteConfirmation({
  alert,
  onOpenChange,
  onConfirm,
  isLoading = false,
}: AlertDeleteConfirmationProps) {
  const details = alert ? priceAlertDeleteDetails(alert) : []

  return (
    <ConfirmationDialog
      open={Boolean(alert)}
      onOpenChange={onOpenChange}
      onConfirm={onConfirm}
      title="Delete alert"
      description="This cannot be undone."
      confirmText="Delete"
      variant="destructive"
      isLoading={isLoading}
    >
      {details.length > 0 ? (
        <dl className="mb-4 space-y-2 text-sm">
          {details.map((row) => (
            <div key={row.label} className="grid grid-cols-[5.5rem_1fr] gap-x-3 gap-y-0.5">
              <dt className="text-muted-foreground">{row.label}</dt>
              <dd className="min-w-0 break-words font-medium">{row.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </ConfirmationDialog>
  )
}
