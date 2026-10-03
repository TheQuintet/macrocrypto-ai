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

/** Ids the title and description take, so the dialog can be named by them. */
const DialogIdsContext = React.createContext<{
  titleId?: string;
  descriptionId?: string;
}>({});

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

/** Keep Tab and Shift+Tab cycling inside the dialog while it is open. */
function trapTab(event: React.KeyboardEvent<HTMLDivElement>) {
  if (event.key !== "Tab") return;

  const focusable = Array.from(
    event.currentTarget.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
  );
  if (focusable.length === 0) {
    event.preventDefault();
    return;
  }

  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  const active = document.activeElement;

  if (event.shiftKey && (active === first || active === event.currentTarget)) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus();
  }
}

export const Dialog: React.FC<DialogProps> = ({ children, open, onOpenChange }) => {
  const titleId = React.useId();
  const descriptionId = React.useId();
  const dialogRef = React.useRef<HTMLDivElement>(null);
  const ids = React.useMemo(
    () => ({ titleId, descriptionId }),
    [titleId, descriptionId],
  );

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

  // Focus moves into the dialog on open and back to its trigger on close.
  React.useEffect(() => {
    if (!open) return;

    const trigger =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialog = dialogRef.current;

    // Only point at a description that rendered; a dangling id names nothing.
    if (dialog && document.getElementById(descriptionId)) {
      dialog.setAttribute("aria-describedby", descriptionId);
    }
    if (dialog && !dialog.contains(document.activeElement)) dialog.focus();

    return () => {
      if (trigger?.isConnected) trigger.focus();
    };
  }, [open, descriptionId]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/50"
        data-testid="dialog-overlay"
        onClick={() => onOpenChange?.(false)}
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onKeyDown={trapTab}
        className="relative z-50 bg-white dark:bg-gray-800 rounded-lg shadow-lg max-w-lg w-full mx-4 p-6 outline-none"
      >
        <DialogIdsContext.Provider value={ids}>{children}</DialogIdsContext.Provider>
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
  <h2
    id={React.useContext(DialogIdsContext).titleId}
    className={cn("text-lg font-semibold", className)}
  >
    {children}
  </h2>
);

export const DialogDescription: React.FC<DialogDescriptionProps> = ({ children }) => (
  <p
    id={React.useContext(DialogIdsContext).descriptionId}
    className="text-sm text-gray-500 dark:text-gray-400"
  >
    {children}
  </p>
);

export const DialogFooter: React.FC<DialogFooterProps> = ({ children, className }) => (
  <div className={cn("flex justify-end gap-2 mt-4", className)}>{children}</div>
);
