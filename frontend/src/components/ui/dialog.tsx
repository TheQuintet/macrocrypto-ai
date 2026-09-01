// src/components/ui/dialog.tsx

import * as React from "react";
import { cn } from "@/lib/utils";

interface DialogProps {
  children: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

interface DialogContentProps {
  children: React.ReactNode;
  className?: string;
}

interface DialogHeaderProps {
  children: React.ReactNode;
}

interface DialogTitleProps {
  children: React.ReactNode;
  className?: string;
}

interface DialogDescriptionProps {
  children: React.ReactNode;
}

interface DialogFooterProps {
  children: React.ReactNode;
  className?: string;
}

export const Dialog: React.FC<DialogProps> = ({ children, open, onOpenChange }) => {
  React.useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onOpenChange?.(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/50"
        data-testid="dialog-overlay"
        onClick={() => onOpenChange?.(false)}
      />
      <div
        role="dialog"
        aria-modal="true"
        className="relative z-50 bg-white dark:bg-gray-800 rounded-lg shadow-lg max-w-lg w-full mx-4 p-6"
      >
        {children}
      </div>
    </div>
  );
};

export const DialogContent: React.FC<DialogContentProps> = ({ children, className }) => (
  <div className={cn("", className)}>{children}</div>
);

export const DialogHeader: React.FC<DialogHeaderProps> = ({ children }) => (
  <div className="mb-4">{children}</div>
);

export const DialogTitle: React.FC<DialogTitleProps> = ({ children, className }) => (
  <h2 className={cn("text-lg font-semibold", className)}>{children}</h2>
);

export const DialogDescription: React.FC<DialogDescriptionProps> = ({ children }) => (
  <p className="text-sm text-gray-500 dark:text-gray-400">{children}</p>
);

export const DialogFooter: React.FC<DialogFooterProps> = ({ children, className }) => (
  <div className={cn("flex justify-end gap-2 mt-4", className)}>{children}</div>
);
