// Type definitions for Electron IPC preload bridge
// This file ensures TypeScript knows about window.electron

interface ModelStatus {
  loaded: boolean;
  model?: string;
  progress?: number;
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

interface DownloadResult {
  success: boolean;
  error?: string;
}

interface ElectronAPI {
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
  platform: string;
  
  // Model Management
  downloadModel: (modelName: string) => Promise<DownloadResult>;
  getModelStatus: () => Promise<ModelStatus>;
  
  // Events
  onModelProgress: (callback: (progress: number) => void) => () => void;
  onModelLoaded: (callback: () => void) => () => void;
  onGraphUpdate: (callback: (data: unknown) => void) => () => void;
}

declare global {
  interface Window {
    electron?: ElectronAPI;
  }
}

export {};
