import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { ipc } from '../services/ipc';

interface ModelStatus {
  loaded: boolean;
  model?: string;
  progress?: number;
  downloading?: boolean;
  error?: string;
}

export const useModelStatus = () => {
  const [status, setStatus] = useState<ModelStatus>({
    loaded: false,
    downloading: false,
  });
  const [loading, setLoading] = useState(false);

  // Check model status
  const checkStatus = useCallback(async () => {
    setLoading(true);
    try {
      // Try API first
      const apiStatus = await api.getModelStatus();
      setStatus({
        loaded: apiStatus.loaded,
        model: apiStatus.model,
        progress: apiStatus.progress,
      });
    } catch (apiError) {
      // Fallback to IPC
      try {
        const ipcStatus = await ipc.getModelStatus();
        setStatus({
          loaded: ipcStatus.loaded,
          model: ipcStatus.model,
          progress: ipcStatus.progress,
        });
      } catch (ipcError) {
        setStatus(prev => ({
          ...prev,
          error: 'Failed to check model status',
          loaded: false,
        }));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Download model
  const downloadModel = useCallback(async (modelName: string) => {
    setStatus(prev => ({ ...prev, downloading: true, progress: 0, error: undefined }));
    
    try {
      // Try IPC first (for Electron)
      if (ipc.isElectronMode()) {
        const result = await ipc.downloadModel(modelName);
        if (result.success) {
          setStatus(prev => ({ ...prev, downloading: false, loaded: true, model: modelName }));
        } else {
          throw new Error(result.error || 'Download failed');
        }
      } else {
        // Fallback to API
        await api.downloadModel(modelName);
        setStatus(prev => ({ ...prev, downloading: false, loaded: true, model: modelName }));
      }
    } catch (error) {
      setStatus(prev => ({
        ...prev,
        downloading: false,
        error: error instanceof Error ? error.message : 'Download failed',
      }));
    }
  }, []);

  // Listen to progress updates (Electron only)
  useEffect(() => {
    if (!ipc.isElectronMode()) return;

    const unsubscribeProgress = ipc.onModelProgress((progress) => {
      setStatus(prev => ({ ...prev, progress }));
    });

    const unsubscribeLoaded = ipc.onModelLoaded(() => {
      setStatus(prev => ({ ...prev, loaded: true, downloading: false, progress: 100 }));
    });

    return () => {
      unsubscribeProgress();
      unsubscribeLoaded();
    };
  }, []);

  // Auto-check on mount
  useEffect(() => {
    checkStatus();
  }, []);

  // Poll for status while downloading
  useEffect(() => {
    if (!status.downloading) return;

    const interval = setInterval(() => {
      checkStatus();
    }, 2000);

    return () => clearInterval(interval);
  }, [status.downloading, checkStatus]);

  return {
    status,
    loading,
    checkStatus,
    downloadModel,
    isReady: status.loaded && !status.downloading,
  };
};
