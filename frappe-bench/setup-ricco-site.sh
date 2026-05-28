#!/bin/bash
# =====================================================
# RICCO ERP - Complete Site Setup Script
# =====================================================
# Creates a new ERPNext site and installs all RICCO apps
#
# Prerequisites:
#   - MariaDB 10.6+ running on localhost:3306
#   - Redis running on localhost:6379
#   - Frappe bench initialized
#
# Usage: ./setup-ricco-site.sh
# =====================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

BENCH_DIR="/home/z/my-project/frappe-bench"
SITE_NAME="ricco.localhost"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  RICCO ERP - Site Setup${NC}"
echo -e "${GREEN}========================================${NC}"

cd $BENCH_DIR

# Check for virtual environment
if [ -d "env" ]; then
    source env/bin/activate
fi

# Check if bench command is available
if ! command -v bench &> /dev/null; then
    echo -e "${RED}Error: bench command not found${NC}"
    echo "Please ensure Frappe bench is properly installed"
    exit 1
fi

# Create new site
if [ -d "sites/$SITE_NAME" ]; then
    echo -e "${YELLOW}Site $SITE_NAME already exists. Skipping creation.${NC}"
else
    echo -e "${BLUE}Creating new site: $SITE_NAME${NC}"

    bench new-site $SITE_NAME \
        --db-root-user root \
        --admin-password admin \
        --install-app frappe \
        --set-default
fi

# Install ERPNext
echo -e "${BLUE}Installing ERPNext...${NC}"
bench --site $SITE_NAME install-app erpnext

# Install all RICCO apps
echo -e "${BLUE}Installing RICCO Apps...${NC}"

RICCO_APPS=(
    "ricco_theme"
    "ricco_pos"
    "ricco_whatsapp"
    "ricco_payments"
    "ricco_woocommerce"
    "ricco_localization"
    "ricco_messaging"
    "ricco_verticals"
    "ricco_ai"
    "ricco_productivity"
)

for app in "${RICCO_APPS[@]}"; do
    echo -e "${BLUE}Installing ${app}...${NC}"
    bench --site $SITE_NAME install-app $app 2>/dev/null || {
        echo -e "${YELLOW}Note: ${app} may need additional setup${NC}"
    }
done

# Run migrations
echo -e "${BLUE}Running migrations...${NC}"
bench --site $SITE_NAME migrate

# Build assets
echo -e "${BLUE}Building assets...${NC}"
bench build

# Enable developer mode
echo -e "${BLUE}Enabling developer mode...${NC}"
bench --site $SITE_NAME set-config developer_mode 1

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Site: $SITE_NAME"
echo "URL: http://localhost:8000"
echo "Admin: Administrator / admin"
echo ""
echo "Start with: bench start"
