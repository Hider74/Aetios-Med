#!/bin/bash
# Production Build Script for macOS/Linux
# Builds complete distributable package for Aetios-Med

set -e

# Parse command line arguments
DOWNLOAD_MODEL=false
if [ "$1" = "--with-model" ]; then
    DOWNLOAD_MODEL=true
fi

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

print_header() {
    echo ""
    echo -e "${CYAN}======================================${NC}"
    echo -e "${CYAN} $1${NC}"
    echo -e "${CYAN}======================================${NC}"
    echo ""
}

print_header "Aetios-Med Production Build"

# Check prerequisites
print_info "Checking prerequisites..."
if ! command -v node &> /dev/null; then
    print_error "Node.js not found. Please install Node.js 18-22"
    exit 1
fi
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.10+"
    exit 1
fi
print_success "Prerequisites satisfied"

# Optional model download
if [ "$DOWNLOAD_MODEL" = true ]; then
    print_header "Downloading AI Model"
    node scripts/download-model.js
fi

# Build process
print_header "Building Frontend"
cd frontend
npm install
npm run build
cd ..
print_success "Frontend built"

print_header "Building Backend"
node scripts/build-backend.js
print_success "Backend built"

print_header "Creating Distributable"
npm install
npm run electron:build
print_success "Distributable created"

print_header "Build Complete!"
echo ""
print_success "Distribution packages created in dist/ folder"
echo ""
if [ "$(uname)" = "Darwin" ]; then
    echo "macOS packages:"
    ls -lh dist/*.dmg 2>/dev/null || true
    ls -lh dist/*.zip 2>/dev/null || true
else
    echo "Linux packages:"
    ls -lh dist/*.AppImage 2>/dev/null || true
    ls -lh dist/*.deb 2>/dev/null || true
fi
echo ""
print_info "You can now distribute these files to users!"
echo ""
