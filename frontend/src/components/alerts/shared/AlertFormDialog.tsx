import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { FormEvent, ReactNode } from 'react';
import { AlertAdvancedSection } from './AlertAdvancedSection';

type AlertFormDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  titleAccessory?: ReactNode;
  toolbar?: ReactNode;
  /** Icon switch for the alert kind, shown next to the title while creating. */
  typeSwitcher?: ReactNode;
  requiredFields: ReactNode;
  advancedFields: ReactNode;
  /** Advanced stays open once expanded, and opens itself on an error inside it. */
  advancedOpen: boolean;
  onAdvancedOpenChange: (open: boolean) => void;
  onSubmit: (event: FormEvent) => void;
  submitLabel: string;
  submitDisabled?: boolean;
  isLoading?: boolean;
};

/** Required fields first, optional settings folded behind "Advanced". */
export function AlertFormDialog({
  open,
  onOpenChange,
  title,
  description,
  titleAccessory,
  toolbar,
  typeSwitcher,
  requiredFields,
  advancedFields,
  advancedOpen,
  onAdvancedOpenChange,
  onSubmit,
  submitLabel,
  submitDisabled = false,
  isLoading = false,
}: AlertFormDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className='max-h-[90vh] overflow-y-auto sm:max-w-[460px]'>
        <DialogHeader>
          <div className='flex items-center justify-between gap-3'>
            <div className='flex min-w-0 items-center gap-3'>
              {typeSwitcher}
              <DialogTitle>{title}</DialogTitle>
            </div>
            {titleAccessory}
          </div>
          {description ? (
            <DialogDescription>{description}</DialogDescription>
          ) : null}
        </DialogHeader>

        <form onSubmit={onSubmit} className='space-y-5 py-2'>
          {toolbar}

          {/* Boxed so the always-on fields read apart from Advanced. */}
          <section
            aria-label='Required'
            className='space-y-4 rounded-lg border border-border bg-muted/30 p-3 sm:p-4'
          >
            {requiredFields}
          </section>

          <AlertAdvancedSection
            open={advancedOpen}
            onOpenChange={onAdvancedOpenChange}
          >
            {advancedFields}
          </AlertAdvancedSection>

          <DialogFooter className='gap-2'>
            <Button
              type='button'
              variant='outline'
              className='min-h-11 sm:min-h-9'
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type='submit'
              className='min-h-11 sm:min-h-9'
              disabled={isLoading || submitDisabled}
            >
              {isLoading ? 'Saving...' : submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
