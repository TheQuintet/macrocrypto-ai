import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
// import { Button } from '@/components/ui/button';
import { Bell, TrendingUp, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';

export type AlertType = 'price' | 'prediction' | 'macro';

interface AlertTypeCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  selected?: boolean;
  onClick: () => void;
  className?: string;
}

const AlertTypeCard: React.FC<AlertTypeCardProps> = ({
  icon,
  title,
  description,
  selected,
  onClick,
  className,
}) => (
  <button
    onClick={onClick}
    className={cn(
      'flex flex-col items-center gap-3 p-6 rounded-lg border-2 transition-all text-left',
      'hover:shadow-md hover:border-primary/50',
      selected
        ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
        : 'border-border bg-background',
      className
    )}
  >
    <div className="p-3 rounded-full bg-primary/10 text-primary">
      {icon}
    </div>
    <div className="text-center">
      <h3 className="font-semibold text-sm">{title}</h3>
      <p className="text-xs text-muted-foreground mt-1">{description}</p>
    </div>
  </button>
);

interface AlertTypeSelectorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (type: AlertType) => void;
}

export const AlertTypeSelector: React.FC<AlertTypeSelectorProps> = ({
  open,
  onOpenChange,
  onSelect,
}) => {
  const [selected, setSelected] = React.useState<AlertType | null>(null);

  const handleSelect = (type: AlertType) => {
    setSelected(type);
    onSelect(type);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Choose Alert Type</DialogTitle>
          <DialogDescription>
            Select the type of alert you want to create. Each alert type has
            different configuration options.
          </DialogDescription>
        </DialogHeader>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 py-4">
          <AlertTypeCard
            icon={<Bell className="h-6 w-6" />}
            title="Price Alert"
            description="Get notified when BTC reaches a specific price level"
            selected={selected === 'price'}
            onClick={() => handleSelect('price')}
          />
          <AlertTypeCard
            icon={<TrendingUp className="h-6 w-6" />}
            title="Prediction Alert"
            description="Get notified when BTC prediction changes significantly"
            selected={selected === 'prediction'}
            onClick={() => handleSelect('prediction')}
          />
          <AlertTypeCard
            icon={<Calendar className="h-6 w-6" />}
            title="Macro Event Alert"
            description="Get notified before major economic events"
            selected={selected === 'macro'}
            onClick={() => handleSelect('macro')}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};
