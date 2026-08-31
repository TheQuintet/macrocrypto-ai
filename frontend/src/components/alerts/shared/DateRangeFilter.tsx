// src/components/alerts/shared/DateRangeFilter.tsx

import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface DateRangeFilterProps {
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  className?: string;
}

export const DateRangeFilter: React.FC<DateRangeFilterProps> = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  className,
}) => {
  return (
    <div className={cn('flex flex-col sm:flex-row gap-3 sm:gap-4', className)}>
      <div className="flex-1 space-y-1">
        <Label htmlFor="start-date" className="text-xs text-muted-foreground">
          From
        </Label>
        <Input
          id="start-date"
          type="date"
          value={startDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          className="h-9 text-sm"
        />
      </div>
      <div className="flex-1 space-y-1">
        <Label htmlFor="end-date" className="text-xs text-muted-foreground">
          To
        </Label>
        <Input
          id="end-date"
          type="date"
          value={endDate}
          onChange={(e) => onEndDateChange(e.target.value)}
          className="h-9 text-sm"
        />
      </div>
    </div>
  );
};
