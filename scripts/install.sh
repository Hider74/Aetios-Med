#!/bin/bash
# Aetios-Med Installation Script for macOS/Linux
# Installs dependencies, sets up environment, and initializes the database

set -e  # Exit on error

echo "======================================"
echo " Aetios-Med Installation"
echo "======================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check Node.js version
echo "Checking prerequisites..."
if ! command -v node &> /dev/null; then
    print_error "Node.js not found. Please install Node.js 18-22 (LTS) from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    print_error "Node.js version must be 18 or higher. Current version: $(node -v)"
    print_error "Please install Node.js 18-22 (LTS recommended) from https://nodejs.org/"
    exit 1
fi
if [ "$NODE_VERSION" -ge 25 ]; then
    print_error "Node.js version $(node -v) is not supported. Please use Node.js 18-22 (LTS recommended)."
    print_error "Node.js v25+ has breaking changes. Install a LTS version from https://nodejs.org/"
    exit 1
fi
print_success "Node.js $(node -v) found"

# Check Python version
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.10+ from https://python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    print_error "Python version must be 3.10 or higher. Current version: $PYTHON_VERSION"
    exit 1
fi
print_success "Python $PYTHON_VERSION found"

echo ""
echo "======================================"
echo " Installing Backend Dependencies"
echo "======================================"
echo ""

# Create virtual environment
cd backend
if [ -d "venv" ]; then
    print_info "Virtual environment already exists, skipping creation"
else
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "pip upgraded"

# Install Python dependencies
print_info "Installing Python dependencies (this may take a few minutes)..."
pip install -r requirements.txt > /dev/null 2>&1
print_success "Python dependencies installed"

# Install PyInstaller
print_info "Installing PyInstaller..."
pip install pyinstaller > /dev/null 2>&1
print_success "PyInstaller installed"

# Build backend executable
print_info "Building backend executable (this may take a few minutes)..."
pyinstaller --onefile run.py --distpath dist --workpath build --specpath . > /dev/null 2>&1
if [ -f "dist/run" ]; then
    print_success "Backend executable built successfully at backend/dist/run"
else
    print_error "Failed to build backend executable"
    exit 1
fi

# Initialize database
print_info "Initializing database..."
python3 -c "
import asyncio
from app.models.database import init_database
from app.config import settings

async def init():
    await init_database(str(settings.database_path))
    print('Database initialized at', settings.database_path)

asyncio.run(init())
" 2>&1
print_success "Database initialized"

# Copy default curriculum if not present
print_info "Setting up curriculum data..."
mkdir -p "${HOME}/Library/Application Support/Aetios-Med/curriculum" 2>/dev/null || \
mkdir -p "${HOME}/.local/share/Aetios-Med/curriculum" 2>/dev/null || true

CURRICULUM_SOURCE="app/data/uk_curriculum.json"
if [ "$(uname)" = "Darwin" ]; then
    CURRICULUM_DEST="${HOME}/Library/Application Support/Aetios-Med/curriculum/uk_curriculum.json"
else
    CURRICULUM_DEST="${HOME}/.local/share/Aetios-Med/curriculum/uk_curriculum.json"
fi

if [ ! -f "$CURRICULUM_DEST" ]; then
    cp "$CURRICULUM_SOURCE" "$CURRICULUM_DEST"
    print_success "UK medical curriculum installed"
else
    print_info "Curriculum already exists, skipping copy"
fi

cd ..

echo ""
echo "======================================"
echo " Installing Frontend Dependencies"
echo "======================================"
echo ""

cd frontend
print_info "Installing frontend dependencies..."
npm install > /dev/null 2>&1
print_success "Frontend dependencies installed"
cd ..

echo ""
echo "======================================"
echo " Installing Root Dependencies"
echo "======================================"
echo ""

print_info "Installing root dependencies..."
npm install > /dev/null 2>&1
print_success "Root dependencies installed"

echo ""
echo "======================================"
echo " Installation Complete! 🎉"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Run the application:"
echo "     ${GREEN}npm start${NC}"
echo ""
echo "  2. On first launch:"
echo "     - Open Settings → Download AI Model"
echo "     - Configure your Anki export folder"
echo "     - Configure your Notability folder (optional)"
echo ""
echo "  3. Start studying!"
echo ""
echo "Documentation: https://github.com/Hider74/Aetios-Med"
echo ""
