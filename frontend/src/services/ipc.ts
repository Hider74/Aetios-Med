// Electron IPC wrapper for main process communication
// Type-safe wrapper around Electron IPC with proper TypeScript types

interface ModelStatus {
  loaded: boolean;
  model?: string;
  progress?: number;
}

interface DownloadResult {
  success: boolean;
  error?: string;
}

interface SystemInfo {
  platform: string;
  arch: string;
  memory: number;
  cpus: number;
}

interface FileFilters {
  name: string;
  extensions: string[];
}

interface SelectFileOptions {
  filters?: FileFilters[];
}

interface ElectronAPI {
  // Model Management
  downloadModel: (modelName: string) => Promise<DownloadResult>;
  getModelStatus: () => Promise<ModelStatus>;
  
  // File System
  selectDirectory: () => Promise<string | null>;
  selectFile: (options?: SelectFileOptions) => Promise<string | null>;
  readFile: (path: string) => Promise<string>;
  writeFile: (path: string, content: string) => Promise<void>;
  
  // Resources
  openExternal: (url: string) => Promise<void>;
  showItemInFolder: (path: string) => Promise<void>;
  
  // Settings
  getSettings: () => Promise<Record<string, unknown>>;
  saveSetting: (key: string, value: unknown) => Promise<boolean>;
  
  // Database
  exportDatabase: () => Promise<string>;
  importDatabase: (path: string) => Promise<void>;
  
  // System
  getSystemInfo: () => Promise<SystemInfo>;
  
  // Events
  onModelProgress: (callback: (progress: number) => void) => () => void;
  onModelLoaded: (callback: () => void) => () => void;
  onGraphUpdate: (callback: (data: unknown) => void) => () => void;
}

// Check if we're running in Electron
const isElectron = (): boolean => {
  return typeof window !== 'undefined' && !!window.electron;
};

// Safe IPC wrapper that falls back gracefully if not in Electron
class IpcService {
  private electron?: ElectronAPI;

  constructor() {
    if (isElectron()) {
      this.electron = window.electron;
    }
  }

  // Model Management
  async downloadModel(modelName: string): Promise<DownloadResult> {
    if (!this.electron) {
      console.warn('IPC not available - running in browser mode');
      return { success: false, error: 'Not running in Electron' };
    }
    return this.electron.downloadModel(modelName);
  }

  async getModelStatus(): Promise<ModelStatus> {
    if (!this.electron) {
      return { loaded: false };
    }
    return this.electron.getModelStatus();
  }

  // File System
  async selectFolder(): Promise<string | null> {
    if (!this.electron) {
      console.warn('File selection not available in browser mode');
      return null;
    }
    return this.electron.selectDirectory();
  }

  async selectFile(filters?: FileFilters[]): Promise<string | null> {
    if (!this.electron) {
      console.warn('File selection not available in browser mode');
      return null;
    }
    return this.electron.selectFile({ filters });
  }

  async readFile(path: string): Promise<string> {
    if (!this.electron) {
      throw new Error('File system access not available in browser mode');
    }
    return this.electron.readFile(path);
  }

  async writeFile(path: string, content: string): Promise<void> {
    if (!this.electron) {
      throw new Error('File system access not available in browser mode');
    }
    return this.electron.writeFile(path, content);
  }

  // Resources
  async openExternal(url: string): Promise<void> {
    if (!this.electron) {
      window.open(url, '_blank');
      return;
    }
    return this.electron.openExternal(url);
  }

  async showItemInFolder(path: string): Promise<void> {
    if (!this.electron) {
      console.warn('Show in folder not available in browser mode');
      return;
    }
    return this.electron.showItemInFolder(path);
  }

  // Settings
  async getSettings(): Promise<Record<string, unknown>> {
    if (!this.electron) {
      // Fallback to localStorage
      const settings = localStorage.getItem('appSettings');
      return settings ? JSON.parse(settings) : {};
    }
    return this.electron.getSettings();
  }

  async saveSetting(key: string, value: unknown): Promise<void> {
    if (!this.electron) {
      // Fallback to localStorage
      const settings = await this.getSettings();
      settings[key] = value;
      localStorage.setItem('appSettings', JSON.stringify(settings));
      return;
    }
    await this.electron.saveSetting(key, value);
  }

  // Database
  async exportDatabase(): Promise<string> {
    if (!this.electron) {
      throw new Error('Database export not available in browser mode');
    }
    return this.electron.exportDatabase();
  }

  async importDatabase(path: string): Promise<void> {
    if (!this.electron) {
      throw new Error('Database import not available in browser mode');
    }
    return this.electron.importDatabase(path);
  }

  // System Info
  async getSystemInfo(): Promise<SystemInfo> {
    if (!this.electron) {
      return {
        platform: 'browser',
        arch: 'unknown',
        memory: 0,
        cpus: navigator.hardwareConcurrency || 0,
      };
    }
    return this.electron.getSystemInfo();
  }

  // Events
  onModelProgress(callback: (progress: number) => void): () => void {
    if (!this.electron) {
      return () => {};
    }
    return this.electron.onModelProgress(callback);
  }

  onModelLoaded(callback: () => void): () => void {
    if (!this.electron) {
      return () => {};
    }
    return this.electron.onModelLoaded(callback);
  }

  onGraphUpdate(callback: (data: unknown) => void): () => void {
    if (!this.electron) {
      return () => {};
    }
    return this.electron.onGraphUpdate(callback);
  }

  isElectronMode(): boolean {
    return !!this.electron;
  }
}

export const ipc = new IpcService();
export default ipc;
