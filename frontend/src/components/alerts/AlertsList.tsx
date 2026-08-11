import { AlertListItem } from '@/components/alerts/AlertListItem'
import type { DraftAlert } from '@/types/alerts'
import { Card, CardContent } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

type AlertsListProps = {
  alerts: DraftAlert[]
  onDelete: (id: string) => void
}

/** Renders the list of draft alert rows. */
export function AlertsList({ alerts, onDelete }: AlertsListProps) {
  return (
    <Card className="py-0">
      <CardContent className="flex flex-col p-0">
        {alerts.map((alert, index) => (
          <div key={alert.id}>
            {index > 0 ? <Separator /> : null}
            <AlertListItem alert={alert} onDelete={onDelete} />
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
