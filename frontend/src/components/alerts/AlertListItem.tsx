import { Bell, Trash2 } from 'lucide-react';
import type { PriceAlert } from '@/types/alerts/priceAlert';
import { AlertStatusBadge } from './shared/AlertStatusBadge';
import { AlertStatusToggle } from './shared/AlertStatusToggle';
import { formatPriceAlertHeadline } from './price/priceAlertRule';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type AlertListItemProps = {
  alert: PriceAlert;
  onDelete: (alert: PriceAlert) => void;
  onEdit?: (alert: PriceAlert) => void;
  onToggleStatus?: (alert: PriceAlert) => void;
};

export function AlertListItem({ alert, onDelete, onEdit, onToggleStatus }: AlertListItemProps) {
  const name = alert.name?.trim() || '';
  const description = alert.description?.trim() || '';
  const headline = formatPriceAlertHeadline(alert.asset, alert.alert_type, alert.threshold_price);

  return (
    <div className="relative flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:gap-4">
      {onEdit ? (
        <button
          type="button"
          aria-label="Edit alert"
          onClick={() => onEdit(alert)}
          className={cn(
            'absolute inset-0 z-0 rounded-md',
            'hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          )}
        />
      ) : null}

      <div className="pointer-events-none relative z-10 flex min-w-0 flex-1 items-start gap-3 sm:items-center sm:gap-4">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
          <Bell className="size-4" />
        </span>
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="truncate text-sm font-medium">
              {name || headline}
            </span>
            {onToggleStatus ? (
              <span className="pointer-events-auto">
                <AlertStatusToggle
                  status={alert.status}
                  onToggle={() => onToggleStatus(alert)}
                />
              </span>
            ) : (
              <AlertStatusBadge status={alert.status} size="sm" />
            )}
            {alert.one_time && (
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                One-time
              </span>
            )}
          </div>
          {name ? (
            <span className="truncate text-xs text-muted-foreground">
              {headline}
            </span>
          ) : null}
          {description ? (
            <span className="truncate text-xs text-muted-foreground">
              {description}
            </span>
          ) : null}
          {alert.triggered_at && (
            <span className="truncate text-xs text-muted-foreground">
              {new Date(alert.triggered_at).toLocaleString()}
            </span>
          )}
        </div>
      </div>

      <div className="relative z-10 flex items-center gap-2">
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Delete alert"
          onClick={() => onDelete(alert)}
          className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
