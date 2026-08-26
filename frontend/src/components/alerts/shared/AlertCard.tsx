import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface AlertCardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export const AlertCard: React.FC<AlertCardProps> = ({
  children,
  className,
  onClick,
  hoverable = true,
}) => {
  return (
    <Card
      className={cn(
        'overflow-hidden transition-all',
        hoverable && 'hover:shadow-md',
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      <CardContent className="p-4">{children}</CardContent>
    </Card>
  );
};