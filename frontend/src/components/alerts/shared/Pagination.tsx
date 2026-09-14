// src/components/alerts/shared/Pagination.tsx

import React from 'react';
import { cn } from '@/lib/utils';
import {
  Pagination as ShadPagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

/**
 * `PaginationLink` sizes every item as a 40px square, which leaves the
 * Previous and Next labels no room. Let those two size to their text instead,
 * and give the page numbers a border so the row reads as separate controls
 * rather than one block.
 */
const STEP_BUTTON_CLASSES = 'h-9 w-auto px-3';
const PAGE_BUTTON_CLASSES =
  'h-9 w-9 border border-border aria-[current=page]:border-transparent';

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  className,
}) => {
  if (totalPages <= 1) return null;

  const getPageNumbers = () => {
    const pages: number[] = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        pages.push(1, 2, 3, 4, -1, totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1, -1, totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
      } else {
        pages.push(1, -1, currentPage - 1, currentPage, currentPage + 1, -1, totalPages);
      }
    }

    return pages;
  };

  return (
    <ShadPagination className={className}>
      <PaginationContent className="gap-2">
        <PaginationItem>
          <PaginationPrevious
            onClick={() => currentPage > 1 && onPageChange(currentPage - 1)}
            className={cn(
              STEP_BUTTON_CLASSES,
              currentPage <= 1 && 'pointer-events-none opacity-50',
            )}
          />
        </PaginationItem>

        {getPageNumbers().map((page, index) => (
          <PaginationItem key={index}>
            {page === -1 ? (
              <PaginationEllipsis />
            ) : (
              <PaginationLink
                onClick={() => onPageChange(page)}
                isActive={page === currentPage}
                className={PAGE_BUTTON_CLASSES}
              >
                {page}
              </PaginationLink>
            )}
          </PaginationItem>
        ))}

        <PaginationItem>
          <PaginationNext
            onClick={() => currentPage < totalPages && onPageChange(currentPage + 1)}
            className={cn(
              STEP_BUTTON_CLASSES,
              currentPage >= totalPages && 'pointer-events-none opacity-50',
            )}
          />
        </PaginationItem>
      </PaginationContent>
    </ShadPagination>
  );
};
