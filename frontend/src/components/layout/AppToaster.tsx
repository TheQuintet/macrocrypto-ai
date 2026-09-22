import { NOTIFICATION_TOAST_DURATION_MS } from '@/components/alerts/shared/ToastNotification';
import { Toaster } from '@/components/ui/sonner';

/** Toast host positioned relative to the sidebar (desktop) or viewport edge (mobile). */
export function AppToaster() {
  return (
    <Toaster
      closeButton
      visibleToasts={8}
      duration={NOTIFICATION_TOAST_DURATION_MS}
      position='bottom-left'
      offset={{
        bottom: '1rem',
        left: '1rem',
      }}
      richColors
    />
  );
}
// import { NOTIFICATION_TOAST_DURATION_MS } from '@/components/alerts/shared/ToastNotification';
// import { useSidebar } from '@/components/ui/sidebar';
// import { Toaster } from '@/components/ui/sonner';

// /** Toast host positioned relative to the sidebar (desktop) or viewport edge (mobile). */
// export function AppToaster() {
//   const { open, isMobile } = useSidebar();

//   return (
//     <Toaster
//       closeButton
//       visibleToasts={8}
//       duration={NOTIFICATION_TOAST_DURATION_MS}
//       position='bottom-left'
//       offset={{
//         bottom: '1rem',
//         left: '1rem',
//       }}
//       richColors
//     />
//   );
// }
