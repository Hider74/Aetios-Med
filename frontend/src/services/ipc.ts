// Electron IPC wrapper for main process communication
// Check if running in Electron environment

interface ElectronAPI {
  // Model Management
  downloadModel: (modelName: string) => Promise<{ success: boolean; error?: string }>;
  getModelStatus: () => Promise<{ loaded: boolean; model?: string; progress?: number }>;
  
  // File System
  selectDirectory: () => Promise<string | null>;
  selectFile: (filters?: any[]) => Promise<string | null>;
  readFile: (path: string) => Promise<string>;
  writeFile: (path: string, content: string) => Promise<void>;
  
  // Resources
  openExternal: (url: string) => Promise<void>;
  showItemInFolder: (path: string) => Promise<void>;
  
  // Settings
  getSettings: () => Promise<Record<string, any>>;
  saveSetting: (key: string, value: any) => Promise<void>;
  
  // Database
  exportDatabase: () => Promise<string>;
  importDatabase: (path: string) => Promise<void>;
  
  // Updates
  checkForUpdates: () => Promise<{ available: boolean; version?: string }>;
  downloadUpdate: () => Promise<void>;
  
  // System
  getSystemInfo: () => Promise<{
    platform: string;
    arch: string;
    memory: number;
    cpus: number;
  }>;
  
  // Events
  onModelProgress: (callback: (progress: number) => void) => () => void;
  onModelLoaded: (callback: () => void) => () => void;
  onGraphUpdate: (callback: (data: any) => void) => () => void;
}

// Check if we're running in Electron
const isElectron = (): boolean => {
  return !!(window as any).electron;
};

// Safe IPC wrapper that falls back gracefully if not in Electron
class IpcService {
  private electron?: ElectronAPI;

  constructor() {
    if (isElectron()) {
      this.electron = (window as any).electron;
    }
  }

  // Model Management
  async downloadModel(modelName: string): Promise<{ success: boolean; error?: string }> {
    if (!this.electron) {
      console.warn('IPC not available - running in browser mode');
      return { success: false, error: 'Not running in Electron' };
    }
    return this.electron.downloadModel(modelName);
  }

  async getModelStatus() {
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

  async selectFile(filters?: any[]): Promise<string | null> {
    if (!this.electron) {
      console.warn('File selection not available in browser mode');
      return null;
    }
    return this.electron.selectFile(filters);
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
  async getSettings(): Promise<Record<string, any>> {
    if (!this.electron) {
      // Fallback to localStorage
      const settings = localStorage.getItem('appSettings');
      return settings ? JSON.parse(settings) : {};
    }
    return this.electron.getSettings();
  }

  async saveSetting(key: string, value: any): Promise<void> {
    if (!this.electron) {
      // Fallback to localStorage
      const settings = await this.getSettings();
      settings[key] = value;
      localStorage.setItem('appSettings', JSON.stringify(settings));
      return;
    }
    return this.electron.saveSetting(key, value);
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
  async getSystemInfo() {
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

  onGraphUpdate(callback: (data: any) => void): () => void {
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
