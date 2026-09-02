import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'

type AlertOneTimeFieldProps = {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
}

/** One repeat control, one explanation — the same on every alert form. */
export function AlertOneTimeField({
  checked,
  onChange,
  disabled = false,
}: AlertOneTimeFieldProps) {
  const hint = checked
    ? 'You are notified for the next occurrence only.'
    : 'You are notified every time this event occurs.'

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-3">
        <Label htmlFor="one_time">One-time</Label>
        <Switch
          id="one_time"
          checked={checked}
          onCheckedChange={onChange}
          disabled={disabled}
        />
      </div>
      <p className="text-xs text-muted-foreground">{hint}</p>
    </div>
  )
}
