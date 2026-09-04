type AlertRepeatBadgeProps = {
  oneTime: boolean
}

/** Says whether an alert fires once or every time. */
export function AlertRepeatBadge({ oneTime }: AlertRepeatBadgeProps) {
  return (
    <span className="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
      {oneTime ? 'One-time' : 'Recurring'}
    </span>
  )
}
