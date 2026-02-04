#!/usr/bin/env node
/**
 * Backend Build Script for Aetios-Med
 * Automates Python backend executable build with PyInstaller
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

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

function printHeader(msg) {
  console.log(`\n${colors.cyan}======================================${colors.reset}`);
  console.log(`${colors.cyan} ${msg}${colors.reset}`);
  console.log(`${colors.cyan}======================================${colors.reset}\n`);
}

const isWindows = process.platform === 'win32';
const backendDir = path.join(process.cwd(), 'backend');
const venvDir = path.join(backendDir, 'venv');
const venvBin = isWindows 
  ? path.join(venvDir, 'Scripts')
  : path.join(venvDir, 'bin');
const pythonCmd = isWindows ? 'python' : 'python3';
const pipCmd = path.join(venvBin, isWindows ? 'pip.exe' : 'pip');
const pyinstallerCmd = path.join(venvBin, isWindows ? 'pyinstaller.exe' : 'pyinstaller');

function checkPython() {
  try {
    execSync(`${pythonCmd} --version`, { stdio: 'pipe' });
    printSuccess('Python found');
    return true;
  } catch (error) {
    printError('Python not found');
    printError('Please install Python 3.10+ from https://python.org/');
    return false;
  }
}

function ensureVenv() {
  if (fs.existsSync(venvDir)) {
    printInfo('Virtual environment exists');
    return true;
  }
  
  printInfo('Creating Python virtual environment...');
  try {
    execSync(`${pythonCmd} -m venv ${venvDir}`, { 
      cwd: backendDir,
      stdio: 'inherit'
    });
    printSuccess('Virtual environment created');
    return true;
  } catch (error) {
    printError('Failed to create virtual environment');
    console.error(error.message);
    return false;
  }
}

function installDependencies() {
  printInfo('Installing Python dependencies...');
  try {
    const requirementsPath = path.join(backendDir, 'requirements.txt');
    execSync(`"${pipCmd}" install -r "${requirementsPath}" --quiet`, { 
      cwd: backendDir,
      stdio: 'inherit',
      shell: true
    });
    printSuccess('Python dependencies installed');
    return true;
  } catch (error) {
    printError('Failed to install Python dependencies');
    console.error(error.message);
    return false;
  }
}

function installPyInstaller() {
  printInfo('Installing PyInstaller...');
  try {
    execSync(`"${pipCmd}" install pyinstaller --quiet`, { 
      cwd: backendDir,
      stdio: 'inherit',
      shell: true
    });
    printSuccess('PyInstaller installed');
    return true;
  } catch (error) {
    printError('Failed to install PyInstaller');
    console.error(error.message);
    return false;
  }
}

function buildExecutable() {
  printInfo('Building backend executable (this may take a few minutes)...');
  try {
    const distPath = path.join(backendDir, 'dist');
    const workPath = path.join(backendDir, 'build');
    
    execSync(
      `"${pyinstallerCmd}" --onefile run.py --distpath "${distPath}" --workpath "${workPath}" --specpath . --log-level ERROR`,
      { 
        cwd: backendDir,
        stdio: 'inherit',
        shell: true
      }
    );
    
    const expectedExe = isWindows 
      ? path.join(distPath, 'run.exe')
      : path.join(distPath, 'run');
    
    if (fs.existsSync(expectedExe)) {
      printSuccess(`Backend executable built successfully at ${path.relative(process.cwd(), expectedExe)}`);
      return true;
    } else {
      printError('Backend executable not found after build');
      return false;
    }
  } catch (error) {
    printError('Failed to build backend executable');
    console.error(error.message);
    return false;
  }
}

function main() {
  printHeader('Building Backend Executable');
  
  if (!fs.existsSync(backendDir)) {
    printError(`Backend directory not found: ${backendDir}`);
    process.exit(1);
  }
  
  const steps = [
    { name: 'Check Python', fn: checkPython },
    { name: 'Ensure Virtual Environment', fn: ensureVenv },
    { name: 'Install Dependencies', fn: installDependencies },
    { name: 'Install PyInstaller', fn: installPyInstaller },
    { name: 'Build Executable', fn: buildExecutable }
  ];
  
  for (const step of steps) {
    if (!step.fn()) {
      printError(`\nBuild failed at step: ${step.name}`);
      process.exit(1);
    }
  }
  
  printSuccess('\nBackend build completed successfully!');
  process.exit(0);
}

main();
