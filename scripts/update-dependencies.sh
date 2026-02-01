#!/bin/bash
# Dependency Update Script for Aetios-Med (macOS/Linux)
# Updates all Python and npm dependencies to their latest versions

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check mode
CHECK_MODE=false
if [[ "$1" == "--check" ]]; then
    CHECK_MODE=true
    print_info "Running in CHECK mode - no updates will be performed"
fi

# Change to project root
cd "$PROJECT_ROOT" || exit 1

print_header "Aetios-Med Dependency Updater"
print_info "Project root: $PROJECT_ROOT"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.10+ and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    print_error "pip is not installed. Please install pip and try again."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ and try again."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm and try again."
    exit 1
fi

# Function to check Python dependencies
check_python_deps() {
    print_header "Checking Python Dependencies (backend/requirements.txt)"
    
    if [[ ! -f "backend/requirements.txt" ]]; then
        print_error "backend/requirements.txt not found!"
        return 1
    fi
    
    cd backend || return 1
    
    print_info "Checking for outdated packages..."
    python3 -m pip list --outdated --format=columns 2>/dev/null || python3 -m pip list --outdated
    
    cd "$PROJECT_ROOT" || return 1
}

# Function to update Python dependencies
update_python_deps() {
    print_header "Updating Python Dependencies (backend/requirements.txt)"
    
    if [[ ! -f "backend/requirements.txt" ]]; then
        print_error "backend/requirements.txt not found!"
        return 1
    fi
    
    cd backend || return 1
    
    print_info "Reading current requirements..."
    
    # Create a temporary file to store package names without versions
    temp_file=$(mktemp)
    
    # Extract package names (handle both == and >= version specifiers)
    grep -v "^#" requirements.txt | grep -v "^$" | sed 's/\[.*\]//g' | sed 's/[><=!].*//' > "$temp_file"
    
    # Update each package
    while IFS= read -r package; do
        if [[ -n "$package" ]]; then
            print_info "Updating $package..."
            if python3 -m pip install --upgrade "$package"; then
                print_success "$package updated successfully"
            else
                print_warning "Failed to update $package (may require manual intervention)"
            fi
        fi
    done < "$temp_file"
    
    rm -f "$temp_file"
    
    print_info "Freezing updated dependencies..."
    python3 -m pip freeze > requirements-new.txt
    
    print_success "Python dependencies updated!"
    print_warning "Review requirements-new.txt and update requirements.txt if satisfied"
    
    cd "$PROJECT_ROOT" || return 1
}

# Function to check npm dependencies
check_npm_deps() {
    local dir=$1
    local name=$2
    
    print_header "Checking npm Dependencies ($name)"
    
    if [[ ! -f "$dir/package.json" ]]; then
        print_error "$dir/package.json not found!"
        return 1
    fi
    
    cd "$dir" || return 1
    
    print_info "Checking for outdated packages..."
    npm outdated || true
    
    cd "$PROJECT_ROOT" || return 1
}

# Function to update npm dependencies
update_npm_deps() {
    local dir=$1
    local name=$2
    
    print_header "Updating npm Dependencies ($name)"
    
    if [[ ! -f "$dir/package.json" ]]; then
        print_error "$dir/package.json not found!"
        return 1
    fi
    
    cd "$dir" || return 1
    
    print_info "Updating packages..."
    
    # Update dependencies
    if npm update; then
        print_success "Dependencies updated successfully"
    else
        print_warning "Some dependencies may have failed to update"
    fi
    
    # Check for major updates available
    print_info "Checking for major version updates..."
    npm outdated || true
    
    print_warning "Major version updates require 'npm install <package>@latest' for each package"
    
    cd "$PROJECT_ROOT" || return 1
}

# Main execution
main() {
    if [[ "$CHECK_MODE" == true ]]; then
        # Check mode - just show what's outdated
        check_python_deps
        check_npm_deps "frontend" "Frontend"
        check_npm_deps "." "Root"
        
        print_header "Summary"
        print_info "Check complete. Run without --check flag to update dependencies."
    else
        # Update mode
        print_warning "This will update all dependencies to their latest compatible versions."
        print_warning "It's recommended to commit any changes before running this script."
        echo ""
        read -p "Continue? (y/N) " -n 1 -r
        echo ""
        
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Update cancelled."
            exit 0
        fi
        
        # Update all dependencies
        update_python_deps
        update_npm_deps "frontend" "Frontend"
        update_npm_deps "." "Root"
        
        print_header "Summary"
        print_success "All dependency updates complete!"
        print_info "Python: Review backend/requirements-new.txt"
        print_info "npm: Check package.json and package-lock.json files"
        print_warning "Test your application thoroughly before committing changes"
        print_warning "Run 'pytest' in backend/ and 'npm test' in frontend/ to verify"
    fi
}

# Run main function
main
