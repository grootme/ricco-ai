#!/bin/bash
# =====================================================
# RICCO ERP - ERPNext Installation Script
# =====================================================
# This script sets up ERPNext using Frappe Bench
#
# Prerequisites:
# - MariaDB 10.6+ running on localhost:3306
# - Redis running on localhost:6379, 6380, 6381
# - Node.js 18+ and npm
# - Python 3.10-3.12
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh
# =====================================================

set -e

BENCH_DIR="/home/z/my-project/frappe-bench"
SITE_NAME="${SITE_NAME:-ricco.localhost}"
DB_ROOT_USER="${DB_ROOT_USER:-root}"
DB_ROOT_PASS="${DB_ROOT_PASS:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  RICCO ERP - ERPNext Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check MariaDB
if command -v mysql &> /dev/null; then
    echo -e "${GREEN}✓ MySQL/MariaDB client found${NC}"
else
    echo -e "${RED}✗ MySQL/MariaDB client not found${NC}"
    echo "  Please install: sudo apt install mariadb-client"
fi

# Check Redis
if command -v redis-cli &> /dev/null; then
    echo -e "${GREEN}✓ Redis client found${NC}"
else
    echo -e "${RED}✗ Redis client not found${NC}"
    echo "  Please install: sudo apt install redis-server"
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VER=$(node --version)
    echo -e "${GREEN}✓ Node.js found: $NODE_VER${NC}"
else
    echo -e "${RED}✗ Node.js not found${NC}"
    exit 1
fi

# Check yarn
if command -v yarn &> /dev/null; then
    echo -e "${GREEN}✓ Yarn found${NC}"
else
    echo -e "${YELLOW}! Yarn not found, installing...${NC}"
    npm install -g yarn
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
cd $BENCH_DIR
source env/bin/activate

# Create new site
echo -e "\n${YELLOW}Creating new site: $SITE_NAME${NC}"
echo "This will prompt for MariaDB root password."
echo ""
bench new-site $SITE_NAME \
    --db-root-user $DB_ROOT_USER \
    --db-root-password "$DB_ROOT_PASS" \
    --admin-password admin \
    --install-app frappe \
    --set-default

# Install ERPNext app
echo -e "\n${YELLOW}Installing ERPNext app...${NC}"
bench --site $SITE_NAME install-app erpnext

# Enable developer mode
echo -e "\n${YELLOW}Enabling developer mode...${NC}"
bench --site $SITE_NAME set-config developer_mode 1

# Build assets
echo -e "\n${YELLOW}Building assets...${NC}"
bench build

# Start the server
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "To start the development server:"
echo "  cd $BENCH_DIR"
echo "  source env/bin/activate"
echo "  bench start"
echo ""
echo "Access ERPNext at: http://localhost:8000"
echo "Default credentials:"
echo "  Username: Administrator"
echo "  Password: admin"
echo ""
