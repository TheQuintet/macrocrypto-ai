import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'

type AlertOneTimeFieldProps = {
  checked: boolean
  onChange: (checked: boolean) => void
  hint?: string
  disabled?: boolean
}

/** One-time toggle — the only repeat control, and it lives on the Alert tab. */
export function AlertOneTimeField({
  checked,
  onChange,
  hint,
  disabled = false,
}: AlertOneTimeFieldProps) {
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
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
    </div>
  )
}
