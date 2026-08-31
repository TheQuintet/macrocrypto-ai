import { AlertListItem } from '@/components/alerts/AlertListItem';
import type { PriceAlert } from '@/types/alerts/priceAlert';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

type AlertsListProps = {
  alerts: PriceAlert[];
  onDelete: (alert: PriceAlert) => void;
  onEdit?: (alert: PriceAlert) => void;
  onToggleStatus?: (alert: PriceAlert) => void;
};

export function AlertsList({ alerts, onDelete, onEdit, onToggleStatus }: AlertsListProps) {
  if (alerts.length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        No alerts found
      </div>
    );
  }

  return (
    <Card className="py-0">
      <CardContent className="flex flex-col p-0">
        {alerts.map((alert, index) => (
          <div key={alert.id}>
            {index > 0 ? <Separator /> : null}
            <AlertListItem
              alert={alert}
              onDelete={onDelete}
              onEdit={onEdit}
              onToggleStatus={onToggleStatus}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}