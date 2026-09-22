import { useState, type FormEvent, type ReactNode } from 'react';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertCircle, Clock } from 'lucide-react';
import { AlertFormDialog } from '@/components/alerts/shared/AlertFormDialog';
import { AlertNotificationFields } from '@/components/alerts/shared/AlertNotificationFields';
import { AlertOneTimeField } from '@/components/alerts/shared/AlertOneTimeField';
import { cn } from '@/lib/utils';
import { MACRO_EVENT_TYPES } from '@/lib/alerts/macroEventMapping';
import type {
  EventTiming,
  EventType,
  MacroAlertDraft,
} from '@/types/alerts/macroAlert';
import {
  MACRO_EVENT_ICONS,
  MACRO_EVENT_TITLES,
  MACRO_TIMING_LABELS,
} from './macroEventCopy';

interface MacroAlertFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (draft: MacroAlertDraft) => void;
  /** Seeds the form when a row is opened; its event cannot be swapped. */
  editingDraft?: MacroAlertDraft | null;
  isLoading?: boolean;
  /** Alert-kind switch, so a mis-picked type can be corrected in place. */
  typeSwitcher?: ReactNode;
}

const TIMING_OPTIONS: EventTiming[] = ['1D', '12H', '1H'];

const emptyDraft = {
  eventType: '' as EventType | '',
  timing: '1D' as EventTiming,
  oneTime: true,
  notifyInApp: true,
  notifyEmail: false,
};

export function MacroAlertForm({
  open,
  onOpenChange,
  onSubmit,
  editingDraft,
  isLoading = false,
  typeSwitcher,
}: MacroAlertFormProps) {
  const isEditing = Boolean(editingDraft);
  const [eventType, setEventType] = useState<EventType | ''>(
    emptyDraft.eventType,
  );
  const [timing, setTiming] = useState<EventTiming>(emptyDraft.timing);
  const [oneTime, setOneTime] = useState(emptyDraft.oneTime);
  const [notifyInApp, setNotifyInApp] = useState(emptyDraft.notifyInApp);
  const [notifyEmail, setNotifyEmail] = useState(emptyDraft.notifyEmail);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [sessionOpen, setSessionOpen] = useState(open);

  const resetForm = () => {
    setEventType(editingDraft?.event_type ?? emptyDraft.eventType);
    setTiming(editingDraft?.timing ?? emptyDraft.timing);
    setOneTime(editingDraft?.one_time ?? emptyDraft.oneTime);
    setNotifyInApp(editingDraft?.notify_in_app ?? emptyDraft.notifyInApp);
    setNotifyEmail(editingDraft?.notify_email ?? emptyDraft.notifyEmail);
    setErrors({});
    setAdvancedOpen(false);
  };

  if (sessionOpen !== open) {
    setSessionOpen(open);
    if (open) {
      resetForm();
    }
  }

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      resetForm();
    }
    onOpenChange(nextOpen);
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!eventType) {
      newErrors.event_type = 'Choose an event.';
    }

    if (!notifyInApp && !notifyEmail) {
      newErrors.notify = 'Choose a notification.';
    }

    setErrors(newErrors);
    if (newErrors.notify) {
      setAdvancedOpen(true);
    }
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!validate() || !eventType) return;

    onSubmit({
      event_type: eventType,
      timing,
      one_time: oneTime,
      notify_in_app: notifyInApp,
      notify_email: notifyEmail,
    });
  };

  return (
    <AlertFormDialog
      open={open}
      onOpenChange={handleOpenChange}
      title={isEditing ? 'Edit macro event alert' : 'New macro event alert'}
      typeSwitcher={typeSwitcher}
      advancedOpen={advancedOpen}
      onAdvancedOpenChange={setAdvancedOpen}
      onSubmit={handleSubmit}
      submitLabel={isEditing ? 'Save changes' : 'Create alert'}
      isLoading={isLoading}
      requiredFields={
        <>
          <fieldset className='space-y-4'>
            <div className='space-y-2'>
              <Label id='macro-event-label'>
                Event <span className='text-destructive'>*</span>
              </Label>
              <Select
                value={eventType}
                onValueChange={(value: string) =>
                  setEventType(value as EventType)
                }
              >
                <SelectTrigger
                  aria-labelledby='macro-event-label'
                  disabled={isEditing}
                  className={cn(
                    'min-h-11 sm:min-h-9',
                    errors.event_type && 'border-destructive',
                  )}
                >
                  {eventType ? (
                    <span className='flex items-center gap-2'>
                      <span>{MACRO_EVENT_ICONS[eventType]}</span>
                      <span>{MACRO_EVENT_TITLES[eventType]}</span>
                    </span>
                  ) : (
                    <SelectValue placeholder='Choose an event to track...' />
                  )}
                </SelectTrigger>
                <SelectContent>
                  {MACRO_EVENT_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      <div className='flex items-center gap-2'>
                        <span>{MACRO_EVENT_ICONS[type]}</span>
                        <span>{MACRO_EVENT_TITLES[type]}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.event_type ? (
                <p className='flex items-center gap-1 text-sm text-destructive'>
                  <AlertCircle className='h-3 w-3' />
                  {errors.event_type}
                </p>
              ) : null}
            </div>

            <div className='space-y-2'>
              <Label id='macro-timing-label'>Notify by</Label>
              <Select
                value={timing}
                onValueChange={(value: string) =>
                  setTiming(value as EventTiming)
                }
              >
                <SelectTrigger
                  aria-labelledby='macro-timing-label'
                  className='min-h-11 sm:min-h-9'
                >
                  <span className='flex items-center gap-2'>
                    <Clock className='h-4 w-4 text-muted-foreground' />
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

          </fieldset>

          <AlertOneTimeField
            checked={oneTime}
            onChange={setOneTime}
            disabled={isLoading}
          />
        </>
      }
      advancedFields={
        <div className='space-y-5'>
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
  );
}
