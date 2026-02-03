import { useEffect } from 'react';

interface KeyboardShortcutHandlers {
  onNavigateDashboard?: () => void;
  onNavigateGraph?: () => void;
  onNavigateChat?: () => void;
  onNavigateStudyPlan?: () => void;
  onFocusChatInput?: () => void;
  onCloseModal?: () => void;
}

export const useKeyboardShortcuts = (handlers: KeyboardShortcutHandlers) => {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Cmd (Mac) or Ctrl (Windows/Linux)
      const isModifierKey = event.metaKey || event.ctrlKey;

      // Navigation shortcuts
      if (isModifierKey && event.key >= '1' && event.key <= '4') {
        event.preventDefault();
        
        switch (event.key) {
          case '1':
            handlers.onNavigateDashboard?.();
            break;
          case '2':
            handlers.onNavigateGraph?.();
            break;
          case '3':
            handlers.onNavigateChat?.();
            break;
          case '4':
            handlers.onNavigateStudyPlan?.();
            break;
        }
        return;
      }

      // Focus chat input (Cmd/Ctrl + K)
      if (isModifierKey && event.key === 'k') {
        event.preventDefault();
        handlers.onFocusChatInput?.();
        return;
      }

      // Close modals/panels (Escape)
      if (event.key === 'Escape') {
        handlers.onCloseModal?.();
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handlers]);
};
