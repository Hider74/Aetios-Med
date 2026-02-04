# Production Build Script for Windows
# Builds complete distributable package for Aetios-Med

param(
    [switch]$WithModel
)

$ErrorActionPreference = "Stop"

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

function Print-Header {
    param($Message)
    Write-Host ""
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host " $Message" -ForegroundColor Cyan
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host ""
}

Print-Header "Aetios-Med Production Build"

# Check prerequisites
Print-Info "Checking prerequisites..."
try {
    $null = node -v
    $null = python --version
    Print-Success "Prerequisites satisfied"
} catch {
    Print-Error "Missing prerequisites. Please install Node.js 18-22 and Python 3.10+"
    exit 1
}

# Optional model download
if ($WithModel) {
    Print-Header "Downloading AI Model"
    node scripts/download-model.js
}

# Build process
Print-Header "Building Frontend"
Set-Location frontend
npm install
npm run build
Set-Location ..
Print-Success "Frontend built"

Print-Header "Building Backend"
node scripts/build-backend.js
Print-Success "Backend built"

Print-Header "Creating Distributable"
npm install
npm run electron:build
Print-Success "Distributable created"

Print-Header "Build Complete!"
Write-Host ""
Print-Success "Distribution packages created in dist/ folder"
Write-Host ""
Write-Host "Windows packages:"
Get-ChildItem -Path dist -Filter *.exe -ErrorAction SilentlyContinue | Format-Table Name, Length -AutoSize
Get-ChildItem -Path dist -Filter *Setup.exe -ErrorAction SilentlyContinue | Format-Table Name, Length -AutoSize
Write-Host ""
Print-Info "You can now distribute these files to users!"
Write-Host ""
