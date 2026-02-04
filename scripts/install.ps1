# Aetios-Med Installation Script for Windows
# Installs dependencies, sets up environment, and initializes the database

param(
    [switch]$WithModel
)

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
        Print-Error "Please install Node.js 18-22 (LTS recommended) from https://nodejs.org/"
        exit 1
    }
    if ($nodeMajor -ge 25) {
        Print-Error "Node.js version $nodeVersion is not supported. Please use Node.js 18-22 (LTS recommended)."
        Print-Error "Node.js v25+ has breaking changes. Install a LTS version from https://nodejs.org/"
        exit 1
    }
    Print-Success "Node.js $nodeVersion found"
} catch {
    Print-Error "Node.js not found. Please install Node.js 18-22 (LTS) from https://nodejs.org/"
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

# Install PyInstaller
Print-Info "Installing PyInstaller..."
pip install pyinstaller --quiet
Print-Success "PyInstaller installed"

# Build backend executable
Print-Info "Building backend executable (this may take a few minutes)..."
pyinstaller --onefile run.py --distpath dist --workpath build --specpath . --log-level ERROR
if (Test-Path "dist\run.exe") {
    Print-Success "Backend executable built successfully at backend\dist\run.exe"
} else {
    Print-Error "Failed to build backend executable"
    Print-Error "Check the PyInstaller output above for errors"
    exit 1
}

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
Write-Host " Optional: Download AI Model" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Handle model download
$ModelDownloaded = $false
if ($WithModel) {
    Print-Info "Downloading AI model (4.5GB)..."
    node scripts/download-model.js
    $ModelDownloaded = $true
} else {
    Print-Info "AI Model Download: You can download the 4.5GB AI model now or later."
    $response = Read-Host "Download AI model now? [Y/n]"
    if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
        Print-Info "Downloading AI model (4.5GB)..."
        node scripts/download-model.js
        $ModelDownloaded = $true
    } else {
        Print-Info "Skipping model download. You can download it later from Settings."
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host " Installation Complete! 🎉" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Start the application:"
Write-Host "     " -NoNewline
Write-Host "npm start" -ForegroundColor Green
Write-Host ""
if ($ModelDownloaded) {
    Write-Host "  2. The app will launch with:"
    Write-Host "     ✓ All dependencies installed"
    Write-Host "     ✓ Backend executable built"
    Write-Host "     ✓ AI model ready (4.5GB downloaded)"
    Write-Host "     ✓ Database initialized"
} else {
    Write-Host "  2. On first launch:"
    Write-Host "     - The app will automatically prompt to download the AI model (4.5GB)"
    Write-Host "     - Or download later from Settings → Download AI Model"
    Write-Host "     - Configure your Anki export folder"
    Write-Host "     - Configure your Notability folder (optional)"
}
Write-Host ""
Write-Host "  3. Configure on first launch:"
Write-Host "     - Set your Anki export folder"
Write-Host "     - Set your notes folder (optional)"
Write-Host "     - Start studying!"
Write-Host ""
Write-Host "Documentation: https://github.com/Hider74/Aetios-Med"
Write-Host ""
