// src/components/alerts/shared/ToastNotification.tsx

import { Bell, Calendar, TrendingUp } from 'lucide-react';
import type { ReactNode } from 'react';
import { toast } from 'sonner';
import { notificationToastClassName } from '@/lib/alerts/notificationToastClassName';
import { cn } from '@/lib/utils';
import type { NotificationType } from '@/types/alerts/notifications';

export type ToastClickHandler = () => void;

type InfoToastOptions = {
  onClick?: ToastClickHandler;
};

type NotificationToastOptions = {
  notificationType: NotificationType;
  duration?: number;
  onClick?: ToastClickHandler;
  /** Stable id so the inbox can dismiss this toast without closing the pile. */
  id?: string;
};

/** How long an in-app notification toast stays visible before auto-dismiss. */
export const NOTIFICATION_TOAST_DURATION_MS = 120_000;

function iconForNotificationType(type: NotificationType): ReactNode {
  switch (type) {
    case 'prediction_alert':
    case 'confidence_alert':
      return <TrendingUp className="size-4" />;
    case 'macro_alert':
      return <Calendar className="size-4" />;
    default:
      return <Bell className="size-4" />;
  }
}

function clickableAction(
  message: string,
  onClick: ToastClickHandler,
  toastId: () => string | number,
) {
  return (
    <button
      type="button"
      aria-label={`Open ${message}`}
      className="absolute inset-0 right-8 z-[1]"
      onPointerDown={(event) => {
        event.stopPropagation();
      }}
      onClick={(event) => {
        event.preventDefault();
        event.stopPropagation();
        onClick();
        toast.dismiss(toastId());
      }}
    />
  );
}

export const showToast = {
  success: (message: string, description?: string) => {
    toast.success(message, {
      description,
      duration: 4000,
    });
  },

  error: (message: string, description?: string) => {
    toast.error(message, {
      description,
      duration: 5000,
    });
  },

  info: (
    message: string,
    description?: string,
    duration = 3000,
    options?: InfoToastOptions,
  ) => {
    let id: string | number = '';
    id = toast.info(message, {
      description,
      duration,
      className: options?.onClick ? 'cursor-pointer' : undefined,
      action: options?.onClick
        ? clickableAction(message, options.onClick, () => id)
        : undefined,
    });
    return id;
  },

  notification: (
    message: string,
    description: string | undefined,
    options: NotificationToastOptions,
  ) => {
    let id: string | number = '';
    id = toast(message, {
      ...(options.id ? { id: options.id } : {}),
      description,
      duration: options.duration ?? NOTIFICATION_TOAST_DURATION_MS,
      icon: iconForNotificationType(options.notificationType),
      className: cn(
        notificationToastClassName(options.notificationType),
        options.onClick ? 'cursor-pointer' : undefined,
      ),
      action: options.onClick
        ? clickableAction(message, options.onClick, () => id)
        : undefined,
    });
    return id;
  },

  warning: (message: string, description?: string) => {
    toast.warning(message, {
      description,
      duration: 4000,
    });
  },

  dismiss: (toastId: string | number) => {
    toast.dismiss(toastId);
  },

  dismissAll: () => {
    toast.dismiss();
  },
};
