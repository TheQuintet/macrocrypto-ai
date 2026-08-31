import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Bell, Calendar, Clock, Mail, Repeat, Repeat1 } from 'lucide-react';
import type { MacroEvent, EventType } from '@/types/alerts/macroAlert';

interface MacroAlertFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userId: string;
  events: MacroEvent[];
  onSubmit: (
    eventType: EventType,
    timing: string,
    notifyInApp: boolean,
    notifyEmail: boolean,
    oneTime: boolean
  ) => void;
}

const timingOptions = [
  { value: '1D', label: '1 day before' },
  { value: '12H', label: '12 hours before' },
  { value: '1H', label: '1 hour before' },
];

const eventIcons: Record<EventType, string> = {
  FED: '🏛️',
  CPI: '📊',
  GDP: '📈',
  EMPLOYMENT: '👔',
};

const eventNames: Record<EventType, string> = {
  FED: 'Federal Reserve Meeting',
  CPI: 'CPI Release',
  GDP: 'GDP Release',
  EMPLOYMENT: 'Employment Report',
};

export const MacroAlertForm: React.FC<MacroAlertFormProps> = ({
  open,
  onOpenChange,
  events,
  onSubmit,
}) => {
  const [selectedEventType, setSelectedEventType] = useState<EventType | ''>('');
  const [timing, setTiming] = useState('1D');
  const [notifyInApp, setNotifyInApp] = useState(true);
  const [notifyEmail, setNotifyEmail] = useState(false);
  const [oneTime, setOneTime] = useState(true);

  const uniqueEventTypes = Array.from(new Set(events.map((e) => e.event_type)));

  const handleSubmit = () => {
    if (!selectedEventType) {
      return;
    }
    onSubmit(
      selectedEventType as EventType,
      timing,
      notifyInApp,
      notifyEmail,
      oneTime
    );
    setSelectedEventType('');
    setTiming('1D');
    setNotifyInApp(true);
    setNotifyEmail(false);
    setOneTime(true);
  };

  const selectedEvent = events.find((e) => e.event_type === selectedEventType);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Set Macro Event Alert
          </DialogTitle>
          <DialogDescription>
            Choose an event and set when you want to be notified.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-2">
            <Label htmlFor="event-select">Select Event</Label>
            <Select
              value={selectedEventType || ''}
              onValueChange={(value) => setSelectedEventType(value as EventType)}
            >
              <SelectTrigger id="event-select">
                <SelectValue placeholder="Choose an event to track..." />
              </SelectTrigger>
              <SelectContent>
                {uniqueEventTypes.length === 0 ? (
                  <div className="px-2 py-4 text-center text-sm text-muted-foreground">
                    No events available
                  </div>
                ) : (
                  uniqueEventTypes.map((eventType) => {
                    const event = events.find((e) => e.event_type === eventType);
                    const isSubscribed = event?.subscribed || false;
                    return (
                      <SelectItem key={eventType} value={eventType}>
                        <div className="flex items-center gap-2">
                          <span>{eventIcons[eventType]}</span>
                          <span>{eventNames[eventType]}</span>
                          <span className="text-xs text-muted-foreground">
                            ({event?.impact || 'MEDIUM'})
                          </span>
                          {isSubscribed && (
                            <span className="text-xs text-green-600 ml-1">✅ Active</span>
                          )}
                        </div>
                      </SelectItem>
                    );
                  })
                )}
              </SelectContent>
            </Select>
          </div>

          {selectedEventType && (
            <div className="rounded-lg border bg-muted/30 p-3 space-y-1">
              <p className="text-sm font-medium flex items-center gap-2">
                <span>{eventIcons[selectedEventType as EventType]}</span>
                {eventNames[selectedEventType as EventType]}
              </p>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>Impact: {selectedEvent?.impact || 'MEDIUM'}</span>
                <span>•</span>
                <span>
                  {selectedEvent?.subscribed ? '✅ Subscribed' : '❌ Not subscribed'}
                </span>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="timing-select">Notify Me</Label>
            <Select value={timing} onValueChange={setTiming}>
              <SelectTrigger id="timing-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {timingOptions.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      {opt.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between pt-2 border-t">
            <div className="flex items-center gap-2">
              {oneTime ? (
                <Repeat1 className="h-4 w-4 text-muted-foreground" />
              ) : (
                <Repeat className="h-4 w-4 text-muted-foreground" />
              )}
              <Label htmlFor="one-time" className="text-sm font-medium">
                {oneTime ? 'One-time alert' : 'Recurring alert'}
              </Label>
            </div>
            <Switch
              id="one-time"
              checked={oneTime}
              onCheckedChange={setOneTime}
            />
          </div>
          <p className="text-xs text-muted-foreground -mt-2">
            {oneTime
              ? 'You will be notified once when this event is triggered.'
              : 'You will be notified every time this event occurs.'}
          </p>

          <div className="space-y-3 pt-2 border-t">
            <p className="text-sm font-medium">Notification Preferences</p>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-muted-foreground" />
                <Label htmlFor="notify-inapp" className="text-sm font-normal">
                  In-app notification
                </Label>
              </div>
              <Switch
                id="notify-inapp"
                checked={notifyInApp}
                onCheckedChange={setNotifyInApp}
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <Label htmlFor="notify-email" className="text-sm font-normal">
                  Email notification
                </Label>
              </div>
              <Switch
                id="notify-email"
                checked={notifyEmail}
                onCheckedChange={setNotifyEmail}
              />
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!selectedEventType}
          >
            <Bell className="h-4 w-4 mr-2" />
            Create Alert
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};