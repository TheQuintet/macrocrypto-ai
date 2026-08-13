import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

// Types
export interface MacroIndicator {
  indicator_name: string;
  time: string;
  current_value: number;
  previous_value: number | null;
  change_percent: number | null;
  trend: '↑' | '↓' | '→';
  source: string;
}

interface MacroIndicatorsProps {
  indicators: MacroIndicator[];
  isLoading?: boolean;
  error?: Error | null;
  className?: string;
}

// Helper function to determine color based on indicator and change
const getColorForIndicator = (
  indicatorName: string, 
  changePercent: number | null
): string => {
  if (changePercent === null) return 'text-muted-foreground';
  
  // For most indicators: positive = good (green), negative = bad (red)
  // For unemployment: negative change = good (green), positive = bad (red)
  const isInverseIndicator = indicatorName.toLowerCase().includes('unemployment') ||
                             indicatorName.toLowerCase().includes('unrate');
  
  const isPositive = changePercent > 0;
  const isNegative = changePercent < 0;
  
  if (isInverseIndicator) {
    if (isNegative) return 'text-green-500';
    if (isPositive) return 'text-red-500';
    return 'text-muted-foreground';
  }
  
  if (isPositive) return 'text-green-500';
  if (isNegative) return 'text-red-500';
  return 'text-muted-foreground';
};

// Helper to get change indicator symbol
const getChangeSymbol = (changePercent: number | null): string => {
  if (changePercent === null) return '→';
  if (changePercent > 0) return '↑';
  if (changePercent < 0) return '↓';
  return '→';
};

// Helper to format the change percentage
const formatChangePercent = (changePercent: number | null): string => {
  if (changePercent === null) return '--';
  return `${changePercent > 0 ? '+' : ''}${changePercent.toFixed(2)}%`;
};

// Format date/time
const formatTimestamp = (timeString: string): string => {
  const date = new Date(timeString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  });
};

export function MacroIndicators({ 
  indicators, 
  isLoading = false, 
  error = null, 
  className 
}: MacroIndicatorsProps) {
  // Memoize the formatted indicators to avoid recalculation
  const formattedIndicators = useMemo(() => {
    return indicators.map(indicator => ({
      ...indicator,
      formattedChange: formatChangePercent(indicator.change_percent),
      color: getColorForIndicator(indicator.indicator_name, indicator.change_percent),
      changeSymbol: getChangeSymbol(indicator.change_percent),
      formattedTime: formatTimestamp(indicator.time),
    }));
  }, [indicators]);

  // Loading state
  if (isLoading) {
    return (
      <div className={cn('grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4', className)}>
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="overflow-hidden">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                <Skeleton className="h-4 w-20" />
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-24 mb-2" />
              <Skeleton className="h-4 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={cn('p-4 text-center text-red-500', className)}>
        <p>Failed to load macroeconomic indicators</p>
        <p className="text-sm text-muted-foreground">{error.message}</p>
      </div>
    );
  }

  // Empty state
  if (!indicators || indicators.length === 0) {
    return (
      <div className={cn('p-4 text-center text-muted-foreground', className)}>
        <p>No macroeconomic data available</p>
      </div>
    );
  }

  return (
    <div className={cn('grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4', className)}>
      {formattedIndicators.map((indicator) => (
        <Card key={indicator.indicator_name} className="overflow-hidden transition-all hover:shadow-md">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              {indicator.indicator_name.replace(/_/g, ' ')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold tabular-nums">
                {indicator.current_value.toFixed(2)}
              </span>
              <span className={cn('text-sm font-medium', indicator.color)}>
                {indicator.changeSymbol} {indicator.formattedChange}
              </span>
            </div>
            <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
              <span>Previous: {indicator.previous_value?.toFixed(2) ?? '--'}</span>
              <span>Updated: {indicator.formattedTime}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default MacroIndicators;
