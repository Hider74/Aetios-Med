# Dependency Update Script for Aetios-Med (Windows)
# Updates all Python and npm dependencies to their latest versions

param(
    [switch]$Check
)

# Color functions for output
function Write-Info {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning-Custom {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Header {
    param($Message)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
}

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Set location to project root
Set-Location $ProjectRoot

Write-Header "Aetios-Med Dependency Updater"
Write-Info "Project root: $ProjectRoot"

if ($Check) {
    Write-Info "Running in CHECK mode - no updates will be performed"
}

# Check if Python is installed
try {
    $pythonVersion = & python --version 2>&1
    Write-Info "Found Python: $pythonVersion"
} catch {
    Write-Error-Custom "Python is not installed or not in PATH. Please install Python 3.10+ and try again."
    exit 1
}

# Check if pip is installed
try {
    $pipVersion = & python -m pip --version 2>&1
    Write-Info "Found pip: $pipVersion"
} catch {
    Write-Error-Custom "pip is not installed. Please install pip and try again."
    exit 1
}

# Check if Node.js is installed
try {
    $nodeVersion = & node --version 2>&1
    Write-Info "Found Node.js: $nodeVersion"
} catch {
    Write-Error-Custom "Node.js is not installed or not in PATH. Please install Node.js 18+ and try again."
    exit 1
}

# Check if npm is installed
try {
    $npmVersion = & npm --version 2>&1
    Write-Info "Found npm: $npmVersion"
} catch {
    Write-Error-Custom "npm is not installed or not in PATH. Please install npm and try again."
    exit 1
}

# Function to check Python dependencies
function Check-PythonDeps {
    Write-Header "Checking Python Dependencies (backend/requirements.txt)"
    
    if (-not (Test-Path "backend/requirements.txt")) {
        Write-Error-Custom "backend/requirements.txt not found!"
        return $false
    }
    
    Push-Location backend
    
    Write-Info "Checking for outdated packages..."
    try {
        python -m pip list --outdated --format=columns 2>&1
    } catch {
        python -m pip list --outdated 2>&1
    }
    
    Pop-Location
    return $true
}

# Function to update Python dependencies
function Update-PythonDeps {
    Write-Header "Updating Python Dependencies (backend/requirements.txt)"
    
    if (-not (Test-Path "backend/requirements.txt")) {
        Write-Error-Custom "backend/requirements.txt not found!"
        return $false
    }
    
    Push-Location backend
    
    Write-Info "Reading current requirements..."
    
    # Read requirements file and extract package names
    $packages = Get-Content requirements.txt | Where-Object { 
        $_ -notmatch "^#" -and $_ -notmatch "^\s*$" 
    } | ForEach-Object {
        # Remove version specifiers and extras
        $_ -replace '\[.*\]', '' -replace '[><=!].*', ''
    }
    
    # Update each package
    foreach ($package in $packages) {
        if ($package.Trim()) {
            Write-Info "Updating $package..."
            try {
                python -m pip install --upgrade $package 2>&1 | Out-Null
                Write-Success "$package updated successfully"
            } catch {
                Write-Warning-Custom "Failed to update $package (may require manual intervention)"
            }
        }
    }
    
    Write-Info "Freezing updated dependencies..."
    python -m pip freeze > requirements-new.txt
    
    Write-Success "Python dependencies updated!"
    Write-Warning-Custom "Review requirements-new.txt and update requirements.txt if satisfied"
    
    Pop-Location
    return $true
}

# Function to check npm dependencies
function Check-NpmDeps {
    param(
        [string]$Dir,
        [string]$Name
    )
    
    Write-Header "Checking npm Dependencies ($Name)"
    
    if (-not (Test-Path "$Dir/package.json")) {
        Write-Error-Custom "$Dir/package.json not found!"
        return $false
    }
    
    Push-Location $Dir
    
    Write-Info "Checking for outdated packages..."
    npm outdated 2>&1
    
    Pop-Location
    return $true
}

# Function to update npm dependencies
function Update-NpmDeps {
    param(
        [string]$Dir,
        [string]$Name
    )
    
    Write-Header "Updating npm Dependencies ($Name)"
    
    if (-not (Test-Path "$Dir/package.json")) {
        Write-Error-Custom "$Dir/package.json not found!"
        return $false
    }
    
    Push-Location $Dir
    
    Write-Info "Updating packages..."
    
    # Update dependencies
    try {
        npm update 2>&1
        Write-Success "Dependencies updated successfully"
    } catch {
        Write-Warning-Custom "Some dependencies may have failed to update"
    }
    
    # Check for major updates available
    Write-Info "Checking for major version updates..."
    npm outdated 2>&1
    
    Write-Warning-Custom "Major version updates require 'npm install <package>@latest' for each package"
    
    Pop-Location
    return $true
}

# Main execution
try {
    if ($Check) {
        # Check mode - just show what's outdated
        Check-PythonDeps
        Check-NpmDeps -Dir "frontend" -Name "Frontend"
        Check-NpmDeps -Dir "." -Name "Root"
        
        Write-Header "Summary"
        Write-Info "Check complete. Run without -Check flag to update dependencies."
    } else {
        # Update mode
        Write-Warning-Custom "This will update all dependencies to their latest compatible versions."
        Write-Warning-Custom "It's recommended to commit any changes before running this script."
        Write-Host ""
        
        $response = Read-Host "Continue? (y/N)"
        
        if ($response -notmatch "^[Yy]$") {
            Write-Info "Update cancelled."
            exit 0
        }
        
        # Update all dependencies
        Update-PythonDeps
        Update-NpmDeps -Dir "frontend" -Name "Frontend"
        Update-NpmDeps -Dir "." -Name "Root"
        
        Write-Header "Summary"
        Write-Success "All dependency updates complete!"
        Write-Info "Python: Review backend/requirements-new.txt"
        Write-Info "npm: Check package.json and package-lock.json files"
        Write-Warning-Custom "Test your application thoroughly before committing changes"
        Write-Warning-Custom "Run 'pytest' in backend/ and 'npm test' in frontend/ to verify"
    }
} catch {
    Write-Error-Custom "An error occurred: $_"
    exit 1
}
