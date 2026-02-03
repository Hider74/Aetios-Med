import React from 'react';
import { Wifi, WifiOff, Download, AlertCircle, Activity } from 'lucide-react';
import { useModelStatus } from '../../hooks/useModelStatus';
import { api } from '../../services/api';

interface TopBarProps {
  title: string;
  subtitle?: string;
}

export const TopBar: React.FC<TopBarProps> = ({ title, subtitle }) => {
  const { status, isReady } = useModelStatus();
  const [isOnline, setIsOnline] = React.useState(navigator.onLine);
  const [backendStatus, setBackendStatus] = React.useState<'connected' | 'disconnected' | 'checking'>('checking');

  React.useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  React.useEffect(() => {
    // Check backend connection on mount and periodically
    const checkBackend = async () => {
      try {
        const health = await api.checkHealth();
        setBackendStatus(health.status === 'ok' ? 'connected' : 'disconnected');
      } catch (error) {
        setBackendStatus('disconnected');
      }
    };

    checkBackend();
    
    // Use exponential backoff: check frequently at first, then less often when stable
    let checkInterval = 5000; // Start with 5 seconds
    let consecutiveSuccesses = 0;
    
    const scheduleNextCheck = () => {
      setTimeout(async () => {
        if (!document.hidden) { // Only check when tab is visible
          await checkBackend();
          
          if (backendStatus === 'connected') {
            consecutiveSuccesses++;
            // Gradually increase interval up to 30 seconds when stable
            checkInterval = Math.min(30000, 5000 + consecutiveSuccesses * 2500);
          } else {
            consecutiveSuccesses = 0;
            checkInterval = 5000; // Check more frequently when disconnected
          }
        }
        scheduleNextCheck();
      }, checkInterval);
    };
    
    scheduleNextCheck();
    
    // Reset check interval when tab becomes visible
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        consecutiveSuccesses = 0;
        checkInterval = 5000;
        checkBackend();
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [backendStatus]);

  const getModelStatusColor = () => {
    if (status.error) return 'text-red-500';
    if (status.downloading) return 'text-yellow-500';
    if (isReady) return 'text-green-500';
    return 'text-gray-500';
  };

  const getModelStatusText = () => {
    if (status.error) return 'Model Error';
    if (status.downloading) return `Downloading... ${status.progress || 0}%`;
    if (isReady) return `Model Ready: ${status.model}`;
    return 'Model Not Loaded';
  };

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
      {/* App Branding and Title */}
      <div className="flex items-center gap-4">
        {/* Aetios Med Logo and Name */}
        <div className="flex items-center gap-2 pr-4 border-r border-gray-300 dark:border-gray-600">
          <img 
            src="/logo.png" 
            alt="Aetios Med Logo" 
            className="h-10 w-10 object-contain"
          />
          <span className="text-xl font-bold text-gray-900 dark:text-white">Aetios Med</span>
        </div>
        
        {/* Page Title */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{title}</h2>
          {subtitle && (
            <p className="text-sm text-gray-600 dark:text-gray-400">{subtitle}</p>
          )}
        </div>
      </div>

      {/* Status Indicators */}
      <div className="flex items-center gap-4">
        {/* Backend Connection Status */}
        <div className="flex items-center gap-2">
          {backendStatus === 'connected' ? (
            <>
              <Activity size={18} className="text-green-500" />
              <span className="text-sm text-gray-600 dark:text-gray-400">Backend Connected</span>
            </>
          ) : backendStatus === 'checking' ? (
            <>
              <Activity size={18} className="text-yellow-500 animate-pulse" />
              <span className="text-sm text-gray-600 dark:text-gray-400">Checking...</span>
            </>
          ) : (
            <>
              <AlertCircle size={18} className="text-red-500" />
              <span className="text-sm text-gray-600 dark:text-gray-400">Backend Offline</span>
            </>
          )}
        </div>

        {/* Network Status */}
        <div className="flex items-center gap-2">
          {isOnline ? (
            <>
              <Wifi size={18} className="text-green-500" />
              <span className="text-sm text-gray-600 dark:text-gray-400">Online</span>
            </>
          ) : (
            <>
              <WifiOff size={18} className="text-orange-500" />
              <span className="text-sm text-gray-600 dark:text-gray-400">Offline</span>
            </>
          )}
        </div>

        {/* Model Status */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-gray-100 dark:bg-gray-700">
          {status.downloading ? (
            <Download size={18} className={getModelStatusColor()} />
          ) : status.error ? (
            <AlertCircle size={18} className={getModelStatusColor()} />
          ) : (
            <div className={`w-2 h-2 rounded-full ${isReady ? 'bg-green-500' : 'bg-gray-400'}`} />
          )}
          <span className={`text-sm font-medium ${getModelStatusColor()}`}>
            {getModelStatusText()}
          </span>
        </div>
      </div>
    </header>
  );
};
