import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Calendar } from 'lucide-react'
import { ConfirmationDialog } from '../shared/ConfirmationDialog'
import { AlertTable } from '../shared/AlertTable'
import { AlertTableEmptyRow } from '../shared/AlertTableEmptyRow'
import { MacroEventRow } from './MacroEventRow'
import type {
  EventImpact,
  MacroEventStatusFilter,
  MacroSubscription,
} from '@/types/alerts/macroAlert'

type MacroCalendarTableProps = {
  subscriptions: MacroSubscription[]
  isLoading: boolean
  error: string | null
  /** Filters live in the toolbar above the table. */
  filter: MacroEventStatusFilter
  impactFilter: EventImpact | 'all'
  onSubscribeChange: (subscriptionId: string, subscribed: boolean) => void
  onDelete: (subscriptionId: string) => void
  onEdit: (subscription: MacroSubscription) => void
  onRetry: () => void
}

export function MacroCalendarTable({
  subscriptions,
  isLoading,
  error,
  filter,
  impactFilter,
  onSubscribeChange,
  onDelete,
  onEdit,
  onRetry,
}: MacroCalendarTableProps) {
  const [deletingSubscription, setDeletingSubscription] = useState<{
    subscriptionId: string
    name: string
  } | null>(
    null,
  )

  const filteredSubscriptions = subscriptions.filter((subscription) => {
    if (filter === 'active' && !subscription.subscribed) return false
    if (filter === 'inactive' && subscription.subscribed) return false
    if (
      impactFilter !== 'all'
      && subscription.impact_filter !== impactFilter
    ) return false
    return true
  })

  const handleDelete = () => {
    if (!deletingSubscription) return
    onDelete(deletingSubscription.subscriptionId)
    setDeletingSubscription(null)
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-0">
          {[1, 2, 3, 4].map((row) => (
            <Skeleton key={row} className="h-16 w-full border-b last:border-0" />
          ))}
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-red-500">{error}</p>
          <Button variant="outline" className="mt-4" onClick={onRetry}>
            Retry
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <AlertTable nameLabel="Event type" detailLabel="Notify">
        {filteredSubscriptions.length === 0 ? (
          <AlertTableEmptyRow
            icon={Calendar}
            message={
              subscriptions.length === 0
                ? 'No macro subscriptions yet'
                : 'No macro subscriptions match your filters'
            }
          />
        ) : (
          filteredSubscriptions.map((subscription) => (
            <MacroEventRow
              key={subscription.event_type}
              subscription={subscription}
              onSubscribeChange={onSubscribeChange}
              onEdit={onEdit}
              onDelete={(subscriptionId) =>
                setDeletingSubscription({
                  subscriptionId,
                  name: subscription.event_type,
                })
              }
            />
          ))
        )}
      </AlertTable>

      <ConfirmationDialog
        open={!!deletingSubscription}
        onOpenChange={() => setDeletingSubscription(null)}
        onConfirm={handleDelete}
        title="Delete alert"
        description={`This removes the alert for "${deletingSubscription?.name}". This cannot be undone.`}
        confirmText="Delete"
        variant="destructive"
      />
    </>
  )
}
