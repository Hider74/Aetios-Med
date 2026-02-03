/**
 * Electron Main Process
 * Manages application window and spawns Python backend.
 */
const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs').promises;
const os = require('os');

let mainWindow = null;
let pythonProcess = null;
const BACKEND_PORT = 8741;
const isDev = process.env.NODE_ENV === 'development';

// Settings storage (in production, consider using electron-store)
let appSettings = {};

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    titleBarStyle: 'hiddenInset',
    show: false
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

async function waitForBackend(maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.get(`http://localhost:${BACKEND_PORT}/api/system/health`, (res) => {
          if (res.statusCode === 200) {
            resolve();
          } else {
            reject(new Error(`Backend returned status ${res.statusCode}`));
          }
        });
        req.on('error', reject);
        req.setTimeout(1000, () => {
          req.destroy();
          reject(new Error('Timeout'));
        });
      });
      console.log(`Backend ready after ${i + 1} attempts`);
      return true;
    } catch (e) {
      // Backend not ready yet
      if (i < maxAttempts - 1) {
        await new Promise(r => setTimeout(r, 1000));
      }
    }
  }
  throw new Error('Backend failed to start within 30 seconds');
}

function startPythonBackend() {
  return new Promise(async (resolve, reject) => {
    if (isDev) {
      // In development, assume backend is started manually
      try {
        await waitForBackend(5);
        resolve();
      } catch (e) {
        console.warn('Backend not running in dev mode');
        resolve();
      }
      return;
    }
    
    const pythonPath = path.join(process.resourcesPath, 'backend', 'run');
    pythonProcess = spawn(pythonPath, [], { 
      stdio: 'pipe',
      detached: false
    });
    
    pythonProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      console.error(`Backend error: ${data}`);
    });
    
    pythonProcess.on('error', (error) => {
      console.error(`Failed to start backend: ${error}`);
      reject(error);
    });
    
    // Wait for backend to be ready
    try {
      await waitForBackend();
      resolve();
    } catch (error) {
      reject(error);
    }
  });
}

function stopPythonBackend() {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM');
    pythonProcess = null;
  }
}

app.whenReady().then(async () => {
  try {
    await startPythonBackend();
    createWindow();
  } catch (error) {
    console.error('Failed to start backend:', error);
    dialog.showErrorBox(
      'Backend Failed to Start',
      'The Python backend failed to start. Please check the logs.'
    );
    app.quit();
  }
});

app.on('window-all-closed', () => {
  stopPythonBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('will-quit', stopPythonBackend);

// ===== IPC Handlers =====

// File System
ipcMain.handle('select-directory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, { 
    properties: ['openDirectory'] 
  });
  return result.filePaths[0] || null;
});

ipcMain.handle('select-file', async (event, options) => {
  const dialogOptions = { 
    properties: ['openFile'],
  };
  if (options?.filters) {
    dialogOptions.filters = options.filters;
  }
  const result = await dialog.showOpenDialog(mainWindow, dialogOptions);
  return result.filePaths[0] || null;
});

ipcMain.handle('read-file', async (event, filePath) => {
  try {
    const content = await fs.readFile(filePath, 'utf-8');
    return content;
  } catch (error) {
    throw new Error(`Failed to read file: ${error.message}`);
  }
});

ipcMain.handle('write-file', async (event, filePath, content) => {
  try {
    await fs.writeFile(filePath, content, 'utf-8');
  } catch (error) {
    throw new Error(`Failed to write file: ${error.message}`);
  }
});

// Resources
ipcMain.handle('open-external', async (event, url) => {
  await shell.openExternal(url);
});

ipcMain.handle('show-item-in-folder', async (event, filePath) => {
  shell.showItemInFolder(filePath);
});

// Settings
ipcMain.handle('get-settings', async () => {
  return appSettings;
});

ipcMain.handle('save-setting', async (event, key, value) => {
  appSettings[key] = value;
  // In production, persist to disk using electron-store or similar
  return true;
});

// Database
ipcMain.handle('export-database', async () => {
  const result = await dialog.showSaveDialog(mainWindow, {
    title: 'Export Database',
    defaultPath: 'aetios-backup.db',
    filters: [{ name: 'Database', extensions: ['db'] }]
  });
  
  if (result.canceled || !result.filePath) {
    throw new Error('Export canceled');
  }
  
  // Copy database file to selected location
  const dbPath = path.join(app.getPath('userData'), 'aetios.db');
  await fs.copyFile(dbPath, result.filePath);
  return result.filePath;
});

ipcMain.handle('import-database', async (event, filePath) => {
  const dbPath = path.join(app.getPath('userData'), 'aetios.db');
  await fs.copyFile(filePath, dbPath);
  // Restart app to use new database
  app.relaunch();
  app.exit(0);
});

// System Info
ipcMain.handle('get-system-info', async () => {
  return {
    platform: process.platform,
    arch: process.arch,
    memory: os.totalmem(),
    cpus: os.cpus().length,
  };
});

// Model Management
ipcMain.handle('download-model', async (event, modelName) => {
  // Make request to backend to download model
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({ model_name: modelName });
    const options = {
      hostname: 'localhost',
      port: BACKEND_PORT,
      path: '/api/system/download-model',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
      }
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve({ success: true });
        } else {
          resolve({ success: false, error: `Status ${res.statusCode}: ${data}` });
        }
      });
    });

    req.on('error', (error) => {
      resolve({ success: false, error: error.message });
    });

    req.write(postData);
    req.end();
  });
});

ipcMain.handle('get-model-status', async () => {
  return new Promise((resolve) => {
    http.get(`http://localhost:${BACKEND_PORT}/api/system/model-status`, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        try {
          const status = JSON.parse(data);
          resolve({ 
            loaded: status.is_loaded || false, 
            model: status.model_path || '',
            progress: status.progress
          });
        } catch (e) {
          resolve({ loaded: false });
        }
      });
    }).on('error', () => {
      resolve({ loaded: false });
    });
  });
});
