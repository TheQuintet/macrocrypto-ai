import React from 'react';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  EVENT_NAMES,
  EVENT_IMPACT_COLORS,
  EVENT_IMPACT_LABELS,
  type EventType,
  type EventImpact,
} from '@/types/alerts/macroAlert';

interface MacroEventItemProps {
  eventType: EventType;
  impact: EventImpact;
  subscribed: boolean;
  onToggle: (subscribed: boolean) => void;
  disabled?: boolean;
}

export const MacroEventItem: React.FC<MacroEventItemProps> = ({
  eventType,
  impact,
  subscribed,
  onToggle,
  disabled = false,
}) => {
  const name = EVENT_NAMES[eventType];
  const impactColor = EVENT_IMPACT_COLORS[impact];
  const impactLabel = EVENT_IMPACT_LABELS[impact];

  return (
    <div
      className={cn(
        'flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-lg border transition-colors',
        subscribed ? 'border-primary/20 bg-primary/5' : 'border-border bg-background'
      )}
    >
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <h4 className="font-medium text-sm">{name}</h4>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="outline" className={cn('text-xs', impactColor)}>
              {impactLabel}
            </Badge>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3 pl-4 sm:pl-0">
        <span className="text-xs text-muted-foreground">
          {subscribed ? 'Subscribed' : 'Unsubscribed'}
        </span>
        <Switch
          checked={subscribed}
          onCheckedChange={onToggle}
          disabled={disabled}
        />
      </div>
    </div>
  );
};
