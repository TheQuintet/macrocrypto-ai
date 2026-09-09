import { useMarkNotificationReadMutation } from '@/hooks/alerts/useMarkNotificationReadMutation';
import { cn } from '@/lib/utils';
import { Bell, TrendingUp, Calendar, AlertCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { InAppNotification } from '@/types/alerts/notifications';

interface NotificationItemProps {
  notification: InAppNotification;
  onNavigate?: () => void;
}

// Define the prediction data type
interface PredictionData {
  previousPrediction?: number;
  newPrediction?: number;
  changePercentage?: number;
  horizon?: '24h' | '7d';
  recommendation?: string;
}

const getIcon = (type: string) => {
  switch (type) {
    case 'price_alert':
      return <Bell className="h-4 w-4" />;
    case 'prediction_alert':
      return <TrendingUp className="h-4 w-4" />;
    case 'confidence_alert':
      return <TrendingUp className="h-4 w-4" />;
    case 'macro_alert':
      return <Calendar className="h-4 w-4" />;
    default:
      return <AlertCircle className="h-4 w-4" />;
  }
};

const getColor = (type: string) => {
  switch (type) {
    case 'price_alert':
      return 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400';
    case 'prediction_alert':
      return 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400';
    case 'confidence_alert':
      return 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400';
    case 'macro_alert':
      return 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400';
    default:
      return 'bg-gray-100 text-gray-600 dark:bg-gray-800/50 dark:text-gray-400';
  }
};

// Helper to extract prediction data from notification
const getPredictionData = (notification: InAppNotification): PredictionData | null => {
  const data = notification.data;
  if (!data || typeof data !== 'object') return null;
  
  const d = data as Record<string, unknown>;
  
  // Check if it has prediction-related properties
  if (
    'previousPrediction' in d ||
    'newPrediction' in d ||
    'changePercentage' in d ||
    'horizon' in d ||
    'recommendation' in d
  ) {
    return d as PredictionData;
  }
  return null;
};

export function NotificationItem({ notification, onNavigate }: NotificationItemProps) {
  const markAsRead = useMarkNotificationReadMutation(notification.user_id);

  const handleClick = async () => {
    if (!notification.read) {
      try {
        await markAsRead.mutateAsync(notification.id);
      } catch (error) {
        console.error('Failed to mark notification as read:', error);
      }
    }
    
    if (onNavigate) {
      onNavigate();
    }
    
    if (notification.action_url) {
      window.location.href = notification.action_url;
    }
  };

  const isPredictionAlert = notification.notification_type === 'prediction_alert' || 
                           notification.notification_type === 'confidence_alert';
  const predictionData = isPredictionAlert ? getPredictionData(notification) : null;

  return (
    <div
      className={cn(
        'flex gap-3 p-3 rounded-lg cursor-pointer transition-colors hover:bg-muted/50',
        !notification.read ? 'bg-muted/30' : '',
        notification.is_archived && 'opacity-50'
      )}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          getColor(notification.notification_type)
        )}
      >
        {getIcon(notification.notification_type)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-medium">{notification.title}</p>
          {predictionData?.horizon && (
            <Badge variant="outline" className="text-xs shrink-0">
              {predictionData.horizon === '24h' ? '24h' : '7d'}
            </Badge>
          )}
        </div>
        
        {/* Show prediction data if available */}
        {predictionData && (predictionData.previousPrediction != null || predictionData.newPrediction != null) && (
          <div className="flex items-center gap-2 mt-1 text-sm">
            <span className="text-muted-foreground">
              {predictionData.previousPrediction?.toFixed(0)} → {predictionData.newPrediction?.toFixed(0)}
            </span>
            {predictionData.changePercentage != null && (
              <Badge 
                variant={predictionData.changePercentage > 0 ? 'default' : 'destructive'} 
                className="text-xs"
              >
                {predictionData.changePercentage > 0 ? '+' : ''}{predictionData.changePercentage.toFixed(1)}%
              </Badge>
            )}
          </div>
        )}
        
        {/* Show recommendation for prediction alerts */}
        {predictionData?.recommendation && (
          <p className="text-sm text-primary mt-1">
            {predictionData.recommendation}
          </p>
        )}
        
        {/* Show regular message if no prediction data or fallback */}
        {(!predictionData || !predictionData.recommendation) && notification.message && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {notification.message}
          </p>
        )}
        
        <p className="text-xs text-muted-foreground mt-1">
          {new Date(notification.created_at).toLocaleString()}
        </p>
      </div>
      {!notification.read && (
        <span className="h-2 w-2 shrink-0 mt-2 rounded-full bg-blue-500" />
      )}
    </div>
  );
}

export default NotificationItem;
