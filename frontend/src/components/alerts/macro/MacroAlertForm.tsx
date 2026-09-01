import { useState, type FormEvent, type ReactNode } from 'react'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { AlertCircle, Clock } from 'lucide-react'
import { AlertFormDialog } from '@/components/alerts/shared/AlertFormDialog'
import { AlertNotificationFields } from '@/components/alerts/shared/AlertNotificationFields'
import { AlertOneTimeField } from '@/components/alerts/shared/AlertOneTimeField'
import type { AlertFormTab } from '@/components/alerts/shared/AlertFormTabs'
import { cn } from '@/lib/utils'
import type {
  EventTiming,
  EventType,
  MacroAlertDraft,
  MacroEvent,
} from '@/types/alerts/macroAlert'
import { MACRO_EVENT_ICONS, MACRO_EVENT_TITLES, MACRO_TIMING_LABELS } from './macroEventCopy'

interface MacroAlertFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  events: MacroEvent[]
  onSubmit: (draft: MacroAlertDraft) => void
  isLoading?: boolean
  /** Alert-kind switch, so a mis-picked type can be corrected in place. */
  typeSwitcher?: ReactNode
}

const TIMING_OPTIONS: EventTiming[] = ['1D', '12H', '1H']

const emptyDraft = {
  eventType: '' as EventType | '',
  timing: '1D' as EventTiming,
  oneTime: true,
  notifyInApp: true,
  notifyEmail: false,
}

export function MacroAlertForm({
  open,
  onOpenChange,
  events,
  onSubmit,
  isLoading = false,
  typeSwitcher,
}: MacroAlertFormProps) {
  const [eventType, setEventType] = useState<EventType | ''>(emptyDraft.eventType)
  const [timing, setTiming] = useState<EventTiming>(emptyDraft.timing)
  const [oneTime, setOneTime] = useState(emptyDraft.oneTime)
  const [notifyInApp, setNotifyInApp] = useState(emptyDraft.notifyInApp)
  const [notifyEmail, setNotifyEmail] = useState(emptyDraft.notifyEmail)
  const [tab, setTab] = useState<AlertFormTab>('alert')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [sessionOpen, setSessionOpen] = useState(open)

  const resetForm = () => {
    setEventType(emptyDraft.eventType)
    setTiming(emptyDraft.timing)
    setOneTime(emptyDraft.oneTime)
    setNotifyInApp(emptyDraft.notifyInApp)
    setNotifyEmail(emptyDraft.notifyEmail)
    setTab('alert')
    setErrors({})
  }

  if (sessionOpen !== open) {
    setSessionOpen(open)
    if (open) {
      resetForm()
    }
  }

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      resetForm()
    }
    onOpenChange(nextOpen)
  }

  const eventTypes = Array.from(new Set(events.map((event) => event.event_type)))
  const selectedEvent = events.find((event) => event.event_type === eventType)

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!eventType) {
      newErrors.event_type = 'Choose an event.'
    }

    if (!notifyInApp && !notifyEmail) {
      newErrors.notify = 'Choose a notification.'
    }

    setErrors(newErrors)
    if (newErrors.event_type) {
      setTab('alert')
    } else if (newErrors.notify) {
      setTab('advanced')
    }
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!validate() || !eventType) return

    onSubmit({
      event_type: eventType,
      timing,
      one_time: oneTime,
      notify_in_app: notifyInApp,
      notify_email: notifyEmail,
    })
  }

  return (
    <AlertFormDialog
      open={open}
      onOpenChange={handleOpenChange}
      title="New macro event alert"
      description="Choose an event and when you want to be notified."
      typeSwitcher={typeSwitcher}
      tab={tab}
      onTabChange={setTab}
      onSubmit={handleSubmit}
      submitLabel="Create alert"
      isLoading={isLoading}
      alertTab={
        <>
          <fieldset className="space-y-3 rounded-lg border border-border bg-muted/30 p-3">
            <div className="space-y-2">
              <Label id="macro-event-label">
                Event <span className="text-destructive">*</span>
              </Label>
              <Select
                value={eventType}
                onValueChange={(value: string) => setEventType(value as EventType)}
              >
                <SelectTrigger
                  aria-labelledby="macro-event-label"
                  className={cn('min-h-11 sm:min-h-9', errors.event_type && 'border-destructive')}
                >
                  {eventType ? (
                    <span className="flex items-center gap-2">
                      <span>{MACRO_EVENT_ICONS[eventType]}</span>
                      <span>{MACRO_EVENT_TITLES[eventType]}</span>
                    </span>
                  ) : (
                    <SelectValue placeholder="Choose an event to track..." />
                  )}
                </SelectTrigger>
                <SelectContent>
                  {eventTypes.length === 0 ? (
                    <div className="px-2 py-4 text-center text-sm text-muted-foreground">
                      No events available
                    </div>
                  ) : (
                    eventTypes.map((type) => (
                      <SelectItem key={type} value={type}>
                        <div className="flex items-center gap-2">
                          <span>{MACRO_EVENT_ICONS[type]}</span>
                          <span>{MACRO_EVENT_TITLES[type]}</span>
                          <span className="text-xs text-muted-foreground">
                            ({events.find((event) => event.event_type === type)?.impact ?? 'MEDIUM'}
                            )
                          </span>
                        </div>
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {errors.event_type ? (
                <p className="flex items-center gap-1 text-sm text-destructive">
                  <AlertCircle className="h-3 w-3" />
                  {errors.event_type}
                </p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label id="macro-timing-label">Notify by</Label>
              <Select
                value={timing}
                onValueChange={(value: string) => setTiming(value as EventTiming)}
              >
                <SelectTrigger
                  aria-labelledby="macro-timing-label"
                  className="min-h-11 sm:min-h-9"
                >
                  <span className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    {MACRO_TIMING_LABELS[timing]}
                  </span>
                </SelectTrigger>
                <SelectContent>
                  {TIMING_OPTIONS.map((option) => (
                    <SelectItem key={option} value={option}>
                      {MACRO_TIMING_LABELS[option]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedEvent ? (
              <p role="status" aria-live="polite" className="rounded-md bg-primary/5 px-3 py-2 text-sm">
                {MACRO_EVENT_TITLES[selectedEvent.event_type]} ·{' '}
                {selectedEvent.impact.toLowerCase()} impact ·{' '}
                {MACRO_TIMING_LABELS[timing].toLowerCase()}
              </p>
            ) : null}
          </fieldset>

          <AlertOneTimeField
            checked={oneTime}
            onChange={setOneTime}
            hint={
              oneTime
                ? 'You are notified for the next occurrence only.'
                : 'You are notified every time this event occurs.'
            }
            disabled={isLoading}
          />
        </>
      }
      advancedTab={
        <div className="space-y-4">
          <AlertNotificationFields
            notifyInApp={notifyInApp}
            notifyEmail={notifyEmail}
            onNotifyInAppChange={setNotifyInApp}
            onNotifyEmailChange={setNotifyEmail}
            error={errors.notify}
            disabled={isLoading}
          />
        </div>
      }
    />
  )
}
