import React from 'react';
import { Wifi, WifiOff, Download, AlertCircle } from 'lucide-react';
import { useModelStatus } from '../../hooks/useModelStatus';

interface TopBarProps {
  title: string;
  subtitle?: string;
}

export const TopBar: React.FC<TopBarProps> = ({ title, subtitle }) => {
  const { status, isReady } = useModelStatus();
  const [isOnline, setIsOnline] = React.useState(navigator.onLine);

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
