import { Bell, Trash2, Pencil } from 'lucide-react';
import type { PriceAlert } from '@/types/alerts/priceAlert';
import { AlertStatusBadge } from './shared/AlertStatusBadge';
import { Button } from '@/components/ui/button';

type AlertListItemProps = {
  alert: PriceAlert;
  onDelete: (alert: PriceAlert) => void;
  onEdit?: (alert: PriceAlert) => void;
};

const alertTypeLabels: Record<string, string> = {
  reaches: 'Reaches',
  crosses_above: 'Crosses Above',
  crosses_below: 'Crosses Below',
};

export function AlertListItem({ alert, onDelete, onEdit }: AlertListItemProps) {
  const typeLabel = alertTypeLabels[alert.alert_type] || alert.alert_type;

  return (
    <div className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:gap-4">
      <div className="flex min-w-0 flex-1 items-start gap-3 sm:items-center sm:gap-4">
        <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
          <Bell className="size-4" />
        </span>
        <div className="flex min-w-0 flex-1 flex-col gap-0.5">
          <div className="flex flex-wrap items-center gap-2">
            <span className="truncate text-sm font-medium">
              {alert.asset} {typeLabel} ${alert.threshold_price.toLocaleString()}
            </span>
            <AlertStatusBadge status={alert.status} size="sm" />
            {alert.one_time && (
              <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                One-time
              </span>
            )}
          </div>
          {alert.name && (
            <span className="truncate text-xs text-muted-foreground">
              {alert.name}
            </span>
          )}
          {alert.description && (
            <span className="truncate text-xs text-muted-foreground">
              {alert.description}
            </span>
          )}
          {alert.triggered_at && (
            <span className="truncate text-xs text-muted-foreground">
              Triggered: {new Date(alert.triggered_at).toLocaleString()}
            </span>
          )}
          <span className="text-xs text-muted-foreground">
            Created: {new Date(alert.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {onEdit && (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Edit alert"
            onClick={() => onEdit(alert)}
            className="h-8 w-8"
          >
            <Pencil className="h-4 w-4" />
          </Button>
        )}
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