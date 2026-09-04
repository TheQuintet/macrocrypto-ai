import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { AlertCircle } from 'lucide-react'

type AlertNotificationFieldsProps = {
  notifyInApp: boolean
  notifyEmail: boolean
  onNotifyInAppChange: (checked: boolean) => void
  onNotifyEmailChange: (checked: boolean) => void
  error?: string
  disabled?: boolean
}

/** Delivery channels shared by every alert form's Advanced tab. */
export function AlertNotificationFields({
  notifyInApp,
  notifyEmail,
  onNotifyInAppChange,
  onNotifyEmailChange,
  error,
  disabled = false,
}: AlertNotificationFieldsProps) {
  return (
    <>
      <div className="flex items-center justify-between gap-3 py-0.5">
        <Label htmlFor="notify_in_app">In the app</Label>
        <Switch
          id="notify_in_app"
          checked={notifyInApp}
          onCheckedChange={onNotifyInAppChange}
          disabled={disabled}
        />
      </div>
      <div className="flex items-center justify-between gap-3 py-0.5">
        <Label htmlFor="notify_email">Email</Label>
        <Switch
          id="notify_email"
          checked={notifyEmail}
          onCheckedChange={onNotifyEmailChange}
          disabled={disabled}
        />
      </div>
      {error ? (
        <p className="flex items-center gap-1 text-sm text-destructive">
          <AlertCircle className="h-3 w-3" />
          {error}
        </p>
      ) : null}
    </>
  )
}
