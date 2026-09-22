import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowUp, ArrowDown, Minus, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { PredictionAlertPreview as PreviewType } from '@/types/alerts/predictionAlert';
import { HORIZON_SHORT_LABELS } from './predictionAlertRule';

interface PredictionAlertPreviewProps {
  preview: PreviewType | null;
  isLoading?: boolean;
}

export function PredictionAlertPreview({ preview, isLoading }: PredictionAlertPreviewProps) {
  if (isLoading) {
    return (
      <Card className="border-dashed">
        <CardContent className="p-4 text-center text-muted-foreground">
          <div className="animate-pulse">Generating preview...</div>
        </CardContent>
      </Card>
    );
  }

  if (!preview) {
    return (
      <Card className="border-dashed">
        <CardContent className="p-4 text-center text-muted-foreground">
          <p className="text-sm">Set threshold and horizon to see a preview</p>
          <p className="text-xs">This shows how the alert will appear when triggered</p>
        </CardContent>
      </Card>
    );
  }

  const { previousPrediction, newPrediction, changePercentage, confidence, recommendation, horizon } =
    preview;
  const isUp = newPrediction > previousPrediction;
  const isDown = newPrediction < previousPrediction;
  const absChange = Math.abs(changePercentage);

  return (
    <Card className="border-primary/20 bg-primary/5">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <TrendingUp className="h-4 w-4 text-primary" />
            Prediction Change Alert
          </CardTitle>
          <Badge variant="outline" className="text-xs">
            {HORIZON_SHORT_LABELS[horizon]}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Previous</p>
            <p className="font-medium">{previousPrediction.toFixed(0)}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground">New</p>
            <p className="font-medium">{newPrediction.toFixed(0)}</p>
          </div>
        </div>

        <div className="flex items-center justify-between rounded-lg bg-background/50 p-2">
          <div className="flex items-center gap-2">
            {isUp ? (
              <ArrowUp className="h-4 w-4 text-green-500" />
            ) : isDown ? (
              <ArrowDown className="h-4 w-4 text-red-500" />
            ) : (
              <Minus className="h-4 w-4 text-yellow-500" />
            )}
            <span
              className={cn(
                'font-medium',
                isUp ? 'text-green-500' : isDown ? 'text-red-500' : 'text-yellow-500',
              )}
            >
              {isUp ? '+' : ''}
              {absChange.toFixed(1)}%
            </span>
          </div>
          <Badge variant="secondary" className="text-xs">
            {confidence.toFixed(0)}% confidence
          </Badge>
        </div>

        <div className="rounded-lg bg-background/50 p-2">
          <p className="text-sm text-center font-medium text-primary">{recommendation}</p>
        </div>

        <div className="flex justify-between text-xs text-muted-foreground">
          <span>🔔 In-app notification</span>
          <span>📧 Email notification</span>
        </div>
      </CardContent>
    </Card>
  );
}
