# Aetios-Med Installation Script for Windows
# Installs dependencies, sets up environment, and initializes the database

$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Aetios-Med Installation" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

function Print-Success {
    param($Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Print-Error {
    param($Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Print-Info {
    param($Message)
    Write-Host "ℹ $Message" -ForegroundColor Yellow
}

# Check Node.js version
Write-Host "Checking prerequisites..."
try {
    $nodeVersion = node -v
    $nodeMajor = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
    if ($nodeMajor -lt 18) {
        Print-Error "Node.js version must be 18 or higher. Current version: $nodeVersion"
        exit 1
    }
    Print-Success "Node.js $nodeVersion found"
} catch {
    Print-Error "Node.js not found. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
}

# Check Python version
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Print-Error "Python version must be 3.10 or higher. Current version: $pythonVersion"
            exit 1
        }
        Print-Success "$pythonVersion found"
    }
} catch {
    Print-Error "Python not found. Please install Python 3.10+ from https://python.org/"
    exit 1
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Installing Backend Dependencies" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to backend
Set-Location backend

# Create virtual environment
if (Test-Path "venv") {
    Print-Info "Virtual environment already exists, skipping creation"
} else {
    Print-Info "Creating Python virtual environment..."
    python -m venv venv
    Print-Success "Virtual environment created"
}

# Activate virtual environment
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Print-Info "Upgrading pip..."
python -m pip install --upgrade pip --quiet
Print-Success "pip upgraded"

# Install Python dependencies
Print-Info "Installing Python dependencies (this may take a few minutes)..."
pip install -r requirements.txt --quiet
Print-Success "Python dependencies installed"

# Initialize database
Print-Info "Initializing database..."
python -c @"
import asyncio
from app.models.database import init_database
from app.config import settings

async def init():
    await init_database(str(settings.database_path))
    print('Database initialized at', settings.database_path)

asyncio.run(init())
"@
Print-Success "Database initialized"

# Copy default curriculum if not present
Print-Info "Setting up curriculum data..."
$curriculumDir = "$env:APPDATA\Aetios-Med\curriculum"
New-Item -ItemType Directory -Force -Path $curriculumDir | Out-Null

$curriculumSource = "app\data\uk_curriculum.json"
$curriculumDest = "$curriculumDir\uk_curriculum.json"

if (-not (Test-Path $curriculumDest)) {
    Copy-Item $curriculumSource $curriculumDest
    Print-Success "UK medical curriculum installed"
} else {
    Print-Info "Curriculum already exists, skipping copy"
}

Set-Location ..

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Installing Frontend Dependencies" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location frontend
Print-Info "Installing frontend dependencies..."
npm install --silent
Print-Success "Frontend dependencies installed"
Set-Location ..

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Installing Root Dependencies" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Print-Info "Installing root dependencies..."
npm install --silent
Print-Success "Root dependencies installed"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Installation Complete! 🎉" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Run the application:"
Write-Host "     " -NoNewline
Write-Host "npm start" -ForegroundColor Green
Write-Host ""
Write-Host "  2. On first launch:"
Write-Host "     - Open Settings → Download AI Model"
Write-Host "     - Configure your Anki export folder"
Write-Host "     - Configure your Notability folder (optional)"
Write-Host ""
Write-Host "  3. Start studying!"
Write-Host ""
Write-Host "Documentation: https://github.com/Hider74/Aetios-Med"
Write-Host ""
