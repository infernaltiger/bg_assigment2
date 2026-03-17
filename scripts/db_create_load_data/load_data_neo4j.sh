#!/bin/bash
# Neo4j Data Loading Script

# This script:
# 1. Activates Python virtual environment
# 2. Creates database schema (tables + indexes)
# 3. Loads all data from cleaned CSV files
#
# Usage: in the git bash shell, be in the directory of the project, run ./scripts/db_create_load_data/load_data_neo4j.sh
#this may take some time depending on your machine specs
# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
VENV_DIR="$PROJECT_DIR/.venv"

# =============================================================================
# COLORS
# =============================================================================
#i aded colors just for fun, it's cool to see them
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

print_step() {
    echo -e "${YELLOW} - $1${NC}"
}

print_success() {
    echo -e "${GREEN} + $1${NC}"
}

print_error() {
    echo -e "${RED}!!!! $1${NC}"
}

print_info() {
    echo -e "${BLUE}! $1${NC}"
}


# =============================================================================
# MAIN SCRIPT
# =============================================================================

clear  # Clear terminal

echo -e "${CYAN}Script Directory:${NC} $SCRIPT_DIR"
echo -e "${CYAN}Project Directory:${NC} $PROJECT_DIR"
echo -e "${CYAN}Virtual Environment:${NC} $VENV_DIR"
echo -e "${CYAN}Start Time:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# -----------------------------------------------------------------------------
# Step 0: Check prerequisites
# -----------------------------------------------------------------------------

print_step "Step 0/2: Checking prerequisites..."

if [ ! -d "$VENV_DIR" ]; then
    print_error "Virtual environment not found at: $VENV_DIR"
    echo "Run: python -m venv .venv && pip install neo4j pandas"
    read -p "Press Enter to exit..."
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/load_data_neo4j.py" ]; then
    print_error "load_data_graph.py not found"
    read -p "Press Enter to exit..."
    exit 1
fi

print_success "All prerequisites checked"
echo ""

# -----------------------------------------------------------------------------
# Step 1: Activate Virtual Environment
# -----------------------------------------------------------------------------

print_step "Step 1/2: Activating virtual environment..."
source "$VENV_DIR/Scripts/activate"
print_success "Virtual environment activated"
echo ""

# -----------------------------------------------------------------------------
# Step 3: Load Data
# -----------------------------------------------------------------------------

print_step "Step 2/2: Loading data to Neo4j..."
print_info "This may take some time"
echo ""

cd "$SCRIPT_DIR"
python -u load_data_neo4j.py
LOAD_EXIT_CODE=$?

if [ $LOAD_EXIT_CODE -eq 0 ]; then
    print_success "Data loading completed"
else
    print_error "Data loading failed (exit code: $LOAD_EXIT_CODE)"
    exit 1
fi
# -----------------------------------------------------------------------------
# Completion
# -----------------------------------------------------------------------------
echo -e "${CYAN}End Time:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Deactivate virtual environment
deactivate

# Don't close immediately - wait for user to press Enter
read -p "Press Enter to exit..."

exit 0