import { useState } from 'react'
import { Plus } from 'lucide-react'
import type { DraftAlert } from '@/types/alerts'
import { AlertsEmptyState } from '@/components/alerts/AlertsEmptyState'
import { AlertsList } from '@/components/alerts/AlertsList'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/button'
import { pageCopy } from '@/constants/navigation'

export function AlertsPage() {
  const page = pageCopy.alerts
  const [alerts, setAlerts] = useState<DraftAlert[]>([])

  const addAlert = () => {
    setAlerts((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        rule: 'New alert rule',
        detail: 'Trigger condition not configured',
      },
    ])
  }

  const removeAlert = (id: string) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== id))
  }

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageHeader title={page.title} description={page.body}>
        <Button type="button" className="w-full sm:w-auto" onClick={addAlert}>
          <Plus data-icon="inline-start" />
          Create alert
        </Button>
      </PageHeader>

      {alerts.length === 0 ? (
        <AlertsEmptyState onCreateAlert={addAlert} />
      ) : (
        <AlertsList alerts={alerts} onDelete={removeAlert} />
      )}
    </div>
  )
}
