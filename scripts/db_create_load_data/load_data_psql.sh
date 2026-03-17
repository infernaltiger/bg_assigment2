#!/bin/bash
# PostgreSQL Data Loading Script
#
# This script:
# 1. Activates Python virtual environment
# 2. Creates database schema (tables + indexes)
# 3. Loads all data from cleaned CSV files
#
# Usage: in the git bash shell, be in the directory of the project, run ./scripts/db_create_load_data/load_data_psql.sh
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

print_step "Step 0/3: Checking prerequisites..."

if [ ! -d "$VENV_DIR" ]; then
    print_error "Virtual environment not found at: $VENV_DIR"
    echo ""
    echo "Please create virtual environment first:"
    echo "  python -m uv init"
    echo "  python -m uv sync"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/create_schema_psql.py" ]; then
    print_error "create_schema_psql.py not found at: $SCRIPT_DIR"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/load_data_psql.py" ]; then
    print_error "load_data_psql.py not found at: $SCRIPT_DIR"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

print_success "All prerequisites checked"
echo ""
echo "------------------------------------------------------------------------"
echo ""

# -----------------------------------------------------------------------------
# Step 1: Activate Virtual Environment
# -----------------------------------------------------------------------------

print_step "Step 1/3: Activating virtual environment..."

source "$VENV_DIR/Scripts/activate"

if [ $? -eq 0 ]; then
    print_success "Virtual environment activated"
    echo -e "${CYAN}Python:${NC} $(which python)"
    echo -e "${CYAN}Python Version:${NC} $(python --version)"
else
    print_error "Failed to activate virtual environment"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "------------------------------------------------------------------------"
echo ""

# -----------------------------------------------------------------------------
# Step 2: Create Database Schema
# -----------------------------------------------------------------------------

print_step "Step 2/3: Creating database schema..."
echo ""

cd "$SCRIPT_DIR"
python -u create_schema_psql.py
SCHEMA_EXIT_CODE=$?

echo ""

if [ $SCHEMA_EXIT_CODE -eq 0 ]; then
    print_success "Schema creation completed"
else
    print_error "Schema creation failed (exit code: $SCHEMA_EXIT_CODE)"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "------------------------------------------------------------------------"
echo ""

# -----------------------------------------------------------------------------
# Step 3: Load Data
# -----------------------------------------------------------------------------

print_step "Step 3/3: Loading data..."
echo ""

python -u load_data_psql.py
LOAD_EXIT_CODE=$?

echo ""

if [ $LOAD_EXIT_CODE -eq 0 ]; then
    print_success "Data loading completed"
else
    print_error "Data loading failed (exit code: $LOAD_EXIT_CODE)"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# -----------------------------------------------------------------------------
# Completion
# -----------------------------------------------------------------------------

echo ""
echo -e "${CYAN}END Time:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
echo "------------------------------------------------------------------------"
echo ""

# Deactivate virtual environment
deactivate

# Don't close immediately - wait for user to press Enter
read -p "Press Enter to exit..."

exit 0