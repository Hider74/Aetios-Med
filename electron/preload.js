const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  // File System
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  selectFile: (options) => ipcRenderer.invoke('select-file', options),
  readFile: (path) => ipcRenderer.invoke('read-file', path),
  writeFile: (path, content) => ipcRenderer.invoke('write-file', path, content),
  
  // Resources
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  showItemInFolder: (path) => ipcRenderer.invoke('show-item-in-folder', path),
  
  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSetting: (key, value) => ipcRenderer.invoke('save-setting', key, value),
  
  // Database
  exportDatabase: () => ipcRenderer.invoke('export-database'),
  importDatabase: (path) => ipcRenderer.invoke('import-database', path),
  
  // System
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  platform: process.platform,
  
  // Model Management
  downloadModel: (modelName) => ipcRenderer.invoke('download-model', modelName),
  getModelStatus: () => ipcRenderer.invoke('get-model-status'),
  
  // Events (simplified - would need more complex implementation for real progress)
  onModelProgress: (callback) => {
    const listener = (event, progress) => callback(progress);
    ipcRenderer.on('model-progress', listener);
    return () => ipcRenderer.removeListener('model-progress', listener);
  },
  onModelLoaded: (callback) => {
    const listener = () => callback();
    ipcRenderer.on('model-loaded', listener);
    return () => ipcRenderer.removeListener('model-loaded', listener);
  },
  onGraphUpdate: (callback) => {
    const listener = (event, data) => callback(data);
    ipcRenderer.on('graph-update', listener);
    return () => ipcRenderer.removeListener('graph-update', listener);
  }
});
