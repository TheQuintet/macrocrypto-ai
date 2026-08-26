// src/pages/AlertsPage.tsx

import { AlertManagement } from '@/components/alerts/AlertManagement';
import { PageHeader } from '@/components/layout/PageHeader';
import { pageCopy } from '@/constants/navigation';

export function AlertsPage() {
  const page = pageCopy.alerts;
  
  // Use the UUID that has alerts
  const userId = 'b5e2102c-c4ac-46f9-95c3-2a3c389399a9';

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
