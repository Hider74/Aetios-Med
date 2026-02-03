import { useEffect, useRef } from 'react';

interface KeyboardShortcutHandlers {
  onNavigateDashboard?: () => void;
  onNavigateGraph?: () => void;
  onNavigateChat?: () => void;
  onNavigateStudyPlan?: () => void;
  onFocusChatInput?: () => void;
  onCloseModal?: () => void;
}

export const useKeyboardShortcuts = (handlers: KeyboardShortcutHandlers) => {
  // Use ref to avoid re-creating event listener on every render
  const handlersRef = useRef(handlers);
  
  useEffect(() => {
    handlersRef.current = handlers;
  }, [handlers]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Cmd (Mac) or Ctrl (Windows/Linux)
      const isModifierKey = event.metaKey || event.ctrlKey;

      // Navigation shortcuts
      if (isModifierKey && event.key >= '1' && event.key <= '4') {
        event.preventDefault();
        
        switch (event.key) {
          case '1':
            handlersRef.current.onNavigateDashboard?.();
            break;
          case '2':
            handlersRef.current.onNavigateGraph?.();
            break;
          case '3':
            handlersRef.current.onNavigateChat?.();
            break;
          case '4':
            handlersRef.current.onNavigateStudyPlan?.();
            break;
        }
        return;
      }

      // Focus chat input (Cmd/Ctrl + K)
      if (isModifierKey && event.key === 'k') {
        event.preventDefault();
        handlersRef.current.onFocusChatInput?.();
        return;
      }

      // Close modals/panels (Escape)
      if (event.key === 'Escape') {
        handlersRef.current.onCloseModal?.();
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);
};
