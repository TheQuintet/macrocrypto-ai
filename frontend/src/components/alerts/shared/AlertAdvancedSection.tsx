import { ChevronRight } from 'lucide-react';
import { useId, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

type AlertAdvancedSectionProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
};

/** Optional settings, folded away until asked for. */
export function AlertAdvancedSection({
  open,
  onOpenChange,
  children,
}: AlertAdvancedSectionProps) {
  const panelId = useId();

  return (
    <div className='rounded-lg border border-border'>
      <button
        type='button'
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => onOpenChange(!open)}
        className='flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
      >
        <ChevronRight
          className={cn('h-4 w-4 transition-transform', open && 'rotate-90')}
        />
        Advanced
      </button>
      <div id={panelId} hidden={!open} className='space-y-4 px-3 pb-4 pt-1'>
        {children}
      </div>
    </div>
  );
}
