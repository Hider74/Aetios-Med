#!/usr/bin/env node
/**
 * AI Model Download Script for Aetios-Med
 * Downloads OpenBioLLM-8B model from HuggingFace with progress tracking
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m'
};

function printSuccess(msg) {
  console.log(`${colors.green}✓${colors.reset} ${msg}`);
}

function printError(msg) {
  console.error(`${colors.red}✗${colors.reset} ${msg}`);
}

function printInfo(msg) {
  console.log(`${colors.yellow}ℹ${colors.reset} ${msg}`);
}

// Model configuration
const MODEL_CONFIG = {
  name: 'llama3-openbio-8b.Q4_K_M.gguf',
  url: 'https://huggingface.co/aaditya/Llama3-OpenBioLLM-8B-GGUF/resolve/main/llama3-openbio-8b.Q4_K_M.gguf',
  size: 4.5 * 1024 * 1024 * 1024, // ~4.5GB in bytes
  sha256: null // Optional: add checksum if available
};

function getModelDirectory() {
  const platform = process.platform;
  const homeDir = require('os').homedir();
  
  let modelDir;
  if (platform === 'darwin') {
    modelDir = path.join(homeDir, 'Library', 'Application Support', 'Aetios-Med', 'models');
  } else if (platform === 'win32') {
    modelDir = path.join(process.env.APPDATA || path.join(homeDir, 'AppData', 'Roaming'), 'Aetios-Med', 'models');
  } else {
    modelDir = path.join(homeDir, '.local', 'share', 'Aetios-Med', 'models');
  }
  
  return modelDir;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function formatTime(seconds) {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const minutes = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${minutes}m ${secs}s`;
}

function drawProgressBar(progress, width = 40) {
  const filled = Math.round(width * progress);
  const empty = width - filled;
  return '[' + '='.repeat(filled) + ' '.repeat(empty) + ']';
}

function verifySHA256(filePath, expectedHash) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('sha256');
    const stream = fs.createReadStream(filePath);
    
    stream.on('data', (data) => hash.update(data));
    stream.on('end', () => {
      const computedHash = hash.digest('hex');
      resolve(computedHash === expectedHash);
    });
    stream.on('error', reject);
  });
}

async function downloadModel(outputPath) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(outputPath);
    let downloadedBytes = 0;
    let lastUpdate = Date.now();
    let lastBytes = 0;
    const startTime = Date.now();
    
    printInfo(`Downloading ${MODEL_CONFIG.name}...`);
    printInfo(`Size: ~${formatBytes(MODEL_CONFIG.size)}`);
    printInfo(`Destination: ${outputPath}`);
    console.log();
    
    https.get(MODEL_CONFIG.url, (response) => {
      if (response.statusCode === 302 || response.statusCode === 301) {
        // Follow redirect
        https.get(response.headers.location, handleResponse).on('error', reject);
      } else {
        handleResponse(response);
      }
    }).on('error', reject);
    
    function handleResponse(response) {
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download: HTTP ${response.statusCode}`));
        return;
      }
      
      const totalBytes = parseInt(response.headers['content-length'] || MODEL_CONFIG.size);
      
      response.on('data', (chunk) => {
        downloadedBytes += chunk.length;
        file.write(chunk);
        
        const now = Date.now();
        if (now - lastUpdate > 500) { // Update every 500ms
          const progress = downloadedBytes / totalBytes;
          const speed = (downloadedBytes - lastBytes) / ((now - lastUpdate) / 1000);
          const eta = (totalBytes - downloadedBytes) / speed;
          
          process.stdout.write('\r' + ' '.repeat(100) + '\r'); // Clear line
          process.stdout.write(
            `${drawProgressBar(progress)} ${Math.round(progress * 100)}% ` +
            `${formatBytes(downloadedBytes)}/${formatBytes(totalBytes)} ` +
            `${formatBytes(speed)}/s ETA: ${formatTime(eta)}`
          );
          
          lastUpdate = now;
          lastBytes = downloadedBytes;
        }
      });
      
      response.on('end', () => {
        file.end();
        const duration = (Date.now() - startTime) / 1000;
        console.log(); // New line after progress bar
        printSuccess(`Download completed in ${formatTime(duration)}`);
        resolve();
      });
      
      response.on('error', (error) => {
        file.end();
        reject(error);
      });
    }
  });
}

async function main() {
  console.log();
  console.log(`${colors.cyan}======================================${colors.reset}`);
  console.log(`${colors.cyan} Aetios-Med AI Model Download${colors.reset}`);
  console.log(`${colors.cyan}======================================${colors.reset}`);
  console.log();
  
  const modelDir = getModelDirectory();
  const modelPath = path.join(modelDir, MODEL_CONFIG.name);
  
  // Check if model already exists
  if (fs.existsSync(modelPath)) {
    const stats = fs.statSync(modelPath);
    printInfo(`Model already exists at: ${modelPath}`);
    printInfo(`Size: ${formatBytes(stats.size)}`);
    
    // Ask if user wants to re-download
    const readline = require('readline').createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    const answer = await new Promise((resolve) => {
      readline.question('Re-download? [y/N] ', (ans) => {
        readline.close();
        resolve(ans.toLowerCase());
      });
    });
    
    if (answer !== 'y' && answer !== 'yes') {
      printInfo('Download cancelled.');
      process.exit(0);
    }
    
    // Delete existing file
    fs.unlinkSync(modelPath);
  }
  
  // Create directory if it doesn't exist
  if (!fs.existsSync(modelDir)) {
    fs.mkdirSync(modelDir, { recursive: true });
    printSuccess(`Created model directory: ${modelDir}`);
  }
  
  try {
    await downloadModel(modelPath);
    
    // Verify checksum if available
    if (MODEL_CONFIG.sha256) {
      printInfo('Verifying file integrity...');
      const isValid = await verifySHA256(modelPath, MODEL_CONFIG.sha256);
      if (isValid) {
        printSuccess('Checksum verified!');
      } else {
        printError('Checksum verification failed!');
        printError('The downloaded file may be corrupted.');
        process.exit(1);
      }
    }
    
    console.log();
    printSuccess('AI model downloaded successfully!');
    printInfo(`Model location: ${modelPath}`);
    console.log();
    
  } catch (error) {
    console.log();
    printError(`Download failed: ${error.message}`);
    console.log();
    printInfo('You can try again or download manually from:');
    printInfo(MODEL_CONFIG.url);
    printInfo(`Save to: ${modelPath}`);
    console.log();
    process.exit(1);
  }
}

// Allow direct execution
if (require.main === module) {
  main().catch((error) => {
    printError(`Unexpected error: ${error.message}`);
    process.exit(1);
  });
}

module.exports = { downloadModel: main, getModelDirectory, MODEL_CONFIG };
