// src/components/ui/pagination.tsx

import * as React from "react";
import { cn } from "@/lib/utils";
import { ChevronLeft, ChevronRight, MoreHorizontal } from "lucide-react";

export const Pagination = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <nav
    role="navigation"
    aria-label="pagination"
    className={cn("mx-auto flex w-full justify-center", className)}
    {...props}
  />
);
Pagination.displayName = "Pagination";

export const PaginationContent = React.forwardRef<
  HTMLUListElement,
  React.HTMLAttributes<HTMLUListElement>
>(({ className, ...props }, ref) => (
  <ul
    ref={ref}
    className={cn("flex flex-row items-center gap-1", className)}
    {...props}
  />
));
PaginationContent.displayName = "PaginationContent";

export const PaginationItem = React.forwardRef<
  HTMLLIElement,
  React.LiHTMLAttributes<HTMLLIElement>
>(({ className, ...props }, ref) => (
  <li ref={ref} className={cn("", className)} {...props} />
));
PaginationItem.displayName = "PaginationItem";

interface PaginationLinkProps {
  isActive?: boolean;
  onClick?: () => void;
  className?: string;
  children: React.ReactNode;
}

export const PaginationLink = ({
  className,
  isActive,
  onClick,
  children,
  ...props
}: PaginationLinkProps) => (
  <button
    onClick={onClick}
    aria-current={isActive ? "page" : undefined}
    className={cn(
      "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
      isActive
        ? "bg-primary text-primary-foreground hover:bg-primary/90"
        : "text-muted-foreground",
      "h-10 w-10",
      className
    )}
    {...props}
  >
    {children}
  </button>
);
PaginationLink.displayName = "PaginationLink";

interface PaginationPreviousProps {
  onClick?: () => void;
  className?: string;
}

export const PaginationPrevious = ({
  className,
  onClick,
  ...props
}: PaginationPreviousProps) => (
  <PaginationLink
    onClick={onClick}
    aria-label="Go to previous page"
    className={cn("gap-1 pl-2.5", className)}
    {...props}
  >
    <ChevronLeft className="h-4 w-4" />
    <span>Previous</span>
  </PaginationLink>
);
PaginationPrevious.displayName = "PaginationPrevious";

interface PaginationNextProps {
  onClick?: () => void;
  className?: string;
}

export const PaginationNext = ({
  className,
  onClick,
  ...props
}: PaginationNextProps) => (
  <PaginationLink
    onClick={onClick}
    aria-label="Go to next page"
    className={cn("gap-1 pr-2.5", className)}
    {...props}
  >
    <span>Next</span>
    <ChevronRight className="h-4 w-4" />
  </PaginationLink>
);
PaginationNext.displayName = "PaginationNext";

export const PaginationEllipsis = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) => (
  <span
    aria-hidden
    className={cn("flex h-10 w-10 items-center justify-center", className)}
    {...props}
  >
    <MoreHorizontal className="h-4 w-4" />
    <span className="sr-only">More pages</span>
  </span>
);
PaginationEllipsis.displayName = "PaginationEllipsis";
