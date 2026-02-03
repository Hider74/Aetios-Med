import React, { useEffect } from 'react';
import { X } from 'lucide-react';

interface UserGuidePanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const UserGuidePanel: React.FC<UserGuidePanelProps> = ({ isOpen, onClose }) => {
  // Handle escape key press
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when guide is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center animate-fadeIn"
      role="dialog"
      aria-modal="true"
      aria-labelledby="user-guide-title"
    >
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-label="Close user guide"
      />
      
      {/* Panel */}
      <div className="relative w-full h-full max-w-7xl max-h-screen mx-4 my-4 flex flex-col bg-white dark:bg-gray-900 rounded-lg shadow-2xl overflow-hidden">
        {/* Header with close button */}
        <div className="flex items-center justify-between px-6 py-4 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <h2 id="user-guide-title" className="text-xl font-semibold text-gray-900 dark:text-white">
            User Guide
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-gray-700 dark:text-gray-300"
            aria-label="Close user guide"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
        
        {/* Iframe content */}
        <div className="flex-1 overflow-hidden">
          <iframe
            src="/INSTRUCTION_MANUAL.html"
            className="w-full h-full border-0"
            title="Aetios-Med User Manual"
            sandbox="allow-same-origin allow-scripts"
          />
        </div>
      </div>
    </div>
  );
};
