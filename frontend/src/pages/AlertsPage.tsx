// src/pages/AlertsPage.tsx

import { AlertManagement } from '@/components/alerts/AlertManagement';
import { PageHeader } from '@/components/layout/PageHeader';
import { pageCopy } from '@/constants/navigation';

export function AlertsPage() {
  const page = pageCopy.alerts;
  
  // TODO: Get user ID from auth context
  // For now, using a placeholder - replace with actual user ID from your auth system
  const userId = 'test-user-123';

  return (
    <div className="flex min-w-0 flex-col gap-4 sm:gap-6">
      <PageHeader 
        title={page.title} 
        description={page.body}
      />
      
      <AlertManagement userId={userId} />
    </div>
  );
}
