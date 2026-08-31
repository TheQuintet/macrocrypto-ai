// src/components/ui/switch.tsx

import * as React from "react";
import { cn } from "@/lib/utils";

interface SwitchProps {
  id?: string;
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  size?: 'sm' | 'default';
  'aria-label'?: string;
}

export const Switch: React.FC<SwitchProps> = ({
  id,
  checked = false,
  onCheckedChange,
  disabled = false,
  className,
  size = 'default',
  'aria-label': ariaLabel,
}) => {
  const compact = size === 'sm';

  return (
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={ariaLabel}
      disabled={disabled}
      className={cn(
        "relative inline-flex items-center rounded-full transition-colors",
        compact ? "h-4 w-7" : "h-6 w-11",
        checked ? "bg-primary" : "bg-gray-300 dark:bg-gray-600",
        disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer",
        className
      )}
      onClick={() => onCheckedChange?.(!checked)}
    >
      <span
        className={cn(
          "inline-block transform rounded-full bg-white transition-transform",
          compact ? "h-3 w-3" : "h-4 w-4",
          checked
            ? compact ? "translate-x-3.5" : "translate-x-6"
            : compact ? "translate-x-0.5" : "translate-x-1"
        )}
      />
    </button>
  );
};
