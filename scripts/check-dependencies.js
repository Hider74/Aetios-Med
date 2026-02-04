#!/usr/bin/env node
/**
 * Dependency Checker for Aetios-Med
 * Validates Node.js and Python versions before build
 */

const { execSync } = require('child_process');

const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
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

function checkNodeVersion() {
  try {
    const version = process.version;
    const major = parseInt(version.slice(1).split('.')[0]);
    
    if (major < 18) {
      printError(`Node.js version must be 18 or higher. Current version: ${version}`);
      printError('Please install Node.js 18-22 (LTS recommended) from https://nodejs.org/');
      return false;
    }
    
    if (major >= 25) {
      printError(`Node.js version ${version} is not supported. Please use Node.js 18-22 (LTS recommended).`);
      printError('Node.js v25+ has breaking changes. Install a LTS version from https://nodejs.org/');
      return false;
    }
    
    printSuccess(`Node.js ${version} found`);
    return true;
  } catch (error) {
    printError(`Failed to check Node.js version: ${error.message}`);
    return false;
  }
}

function checkPythonVersion() {
  try {
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    const version = execSync(`${pythonCmd} --version`, { encoding: 'utf8' }).trim();
    
    const match = version.match(/Python (\d+)\.(\d+)/);
    if (!match) {
      printError('Could not parse Python version');
      return false;
    }
    
    const major = parseInt(match[1]);
    const minor = parseInt(match[2]);
    
    if (major < 3 || (major === 3 && minor < 10)) {
      printError(`Python version must be 3.10 or higher. Current version: ${version}`);
      printError('Please install Python 3.10+ from https://python.org/');
      return false;
    }
    
    printSuccess(`${version} found`);
    return true;
  } catch (error) {
    printError('Python not found. Please install Python 3.10+ from https://python.org/');
    return false;
  }
}

function checkNpmAvailability() {
  try {
    const version = execSync('npm --version', { encoding: 'utf8' }).trim();
    printSuccess(`npm ${version} found`);
    return true;
  } catch (error) {
    printError('npm not found. Please install Node.js from https://nodejs.org/');
    return false;
  }
}

function main() {
  console.log('Checking dependencies...\n');
  
  const checks = [
    checkNodeVersion(),
    checkPythonVersion(),
    checkNpmAvailability()
  ];
  
  if (checks.every(check => check)) {
    printInfo('\nAll dependencies satisfied!');
    process.exit(0);
  } else {
    printError('\nSome dependencies are missing or invalid.');
    printError('Please install the required dependencies and try again.');
    process.exit(1);
  }
}

main();
