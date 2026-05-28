#!/bin/bash
# ============================================================================
# RICCO ERP - Frappe v16 Migration Script
# Target: Frappe Framework v16 (Current Stable Release)
# Generated: April 26, 2026
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BENCH_PATH="/home/z/my-project/frappe-bench-v16"
SITE_NAME="ricco-dev.local"
FRAPPE_BRANCH="version-16"
PYTHON_VERSION="3.10"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  RICCO ERP Migration to Frappe v16${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}[1/7] Checking prerequisites...${NC}"

if command -v python3 &> /dev/null; then
    PYTHON_VER=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "  ${GREEN}✓${NC} Python version: $PYTHON_VER"
else
    echo -e "  ${RED}✗${NC} Python 3 not found. Please install Python 3.10+"
    exit 1
fi

if command -v node &> /dev/null; then
    NODE_VER=$(node --version 2>&1)
    echo -e "  ${GREEN}✓${NC} Node.js version: $NODE_VER"
else
    echo -e "  ${RED}✗${NC} Node.js not found. Please install Node.js 18.x LTS"
    exit 1
fi

if command -v mariadb &> /dev/null || command -v mysql &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} MariaDB/MySQL found"
else
    echo -e "  ${YELLOW}!${NC} MariaDB not found. Will need configuration."
fi

if command -v redis-server &> /dev/null || command -v redis-cli &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Redis found"
else
    echo -e "  ${YELLOW}!${NC} Redis not found. Will need configuration."
fi

echo ""

# Phase 1: Initialize Bench
echo -e "${YELLOW}[2/7] Initializing Frappe Bench v16...${NC}"

if [ -d "$BENCH_PATH" ]; then
    echo -e "  ${YELLOW}!${NC} Bench directory exists at $BENCH_PATH"
    read -p "  Remove and recreate? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$BENCH_PATH"
    else
        echo -e "  ${RED}✗${NC} Migration cancelled."
        exit 1
    fi
fi

bench init "$BENCH_PATH" --frappe-branch "$FRAPPE_BRANCH" --python "$PYTHON_VERSION"
cd "$BENCH_PATH"

echo -e "  ${GREEN}✓${NC} Bench initialized successfully"
echo ""

# Phase 2: Create Site
echo -e "${YELLOW}[3/7] Creating development site...${NC}"

read -sp "  Enter MariaDB root password: " MARIADB_ROOT_PASSWORD
echo ""
read -sp "  Enter Admin password for site: " ADMIN_PASSWORD
echo ""

bench new-site "$SITE_NAME" \
    --mariadb-root-password "$MARIADB_ROOT_PASSWORD" \
    --admin-password "$ADMIN_PASSWORD" \
    --install-app frappe

echo -e "  ${GREEN}✓${NC} Site created: $SITE_NAME"
echo ""

# Phase 3: Install ERPNext
echo -e "${YELLOW}[4/7] Installing ERPNext v16...${NC}"

bench get-app erpnext --branch version-16
bench --site "$SITE_NAME" install-app erpnext

echo -e "  ${GREEN}✓${NC} ERPNext installed"
echo ""

# Phase 4: Install Core Apps
echo -e "${YELLOW}[5/7] Installing core applications...${NC}"

# Payments
bench get-app payments --branch version-16
bench --site "$SITE_NAME" install-app payments

# CRM (main branch compatible with v16)
bench get-app crm --branch main
bench --site "$SITE_NAME" install-app crm

# Helpdesk
bench get-app helpdesk --branch main
bench --site "$SITE_NAME" install-app helpdesk

# Lending
bench get-app lending --branch version-16
bench --site "$SITE_NAME" install-app lending

# Webshop
bench get-app webshop --branch version-16
bench --site "$SITE_NAME" install-app webshop

echo -e "  ${GREEN}✓${NC} Core applications installed"
echo ""

# Phase 5: Install Commerce Apps
echo -e "${YELLOW}[6/7] Installing commerce applications...${NC}"

# E-commerce Integrations
bench get-app ecommerce_integrations --branch version-16
bench --site "$SITE_NAME" install-app ecommerce_integrations

# WooCommerce Connector
bench get-app https://github.com/libracore/woocommerceconnector
bench --site "$SITE_NAME" install-app woocommerceconnector

# POSNext
bench get-app https://github.com/DeeloaSociety/posnext
bench --site "$SITE_NAME" install-app pos_next

# ERPNext Restaurant
bench get-app https://github.com/alphabit-technology/erpnext-restaurant
bench --site "$SITE_NAME" install-app restaurant_management

echo -e "  ${GREEN}✓${NC} Commerce applications installed"
echo ""

# Phase 6: Install Analytics & Communication
echo -e "${YELLOW}[7/7] Installing analytics and communication apps...${NC}"

# Raven (messaging)
bench get-app raven --branch main
bench --site "$SITE_NAME" install-app raven

# Insights (BI)
bench get-app insights --branch version-16
bench --site "$SITE_NAME" install-app insights

# Wiki
bench get-app wiki --branch version-16
bench --site "$SITE_NAME" install-app wiki

# LMS
bench get-app lms --branch version-16
bench --site "$SITE_NAME" install-app lms

# Drive
bench get-app drive --branch version-16
bench --site "$SITE_NAME" install-app drive

# Builder
bench get-app builder --branch version-16
bench --site "$SITE_NAME" install-app builder

# Print Designer
bench get-app print_designer --branch version-16
bench --site "$SITE_NAME" install-app print_designer

echo -e "  ${GREEN}✓${NC} Analytics and communication apps installed"
echo ""

# Summary
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Migration Phase 1 Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Installed applications:"
echo -e "  ${BLUE}•${NC} frappe (v16)"
echo -e "  ${BLUE}•${NC} erpnext (v16)"
echo -e "  ${BLUE}•${NC} payments (v16)"
echo -e "  ${BLUE}•${NC} crm"
echo -e "  ${BLUE}•${NC} helpdesk"
echo -e "  ${BLUE}•${NC} lending (v16)"
echo -e "  ${BLUE}•${NC} webshop (v16)"
echo -e "  ${BLUE}•${NC} ecommerce_integrations (v16)"
echo -e "  ${BLUE}•${NC} woocommerceconnector"
echo -e "  ${BLUE}•${NC} pos_next"
echo -e "  ${BLUE}•${NC} restaurant_management"
echo -e "  ${BLUE}•${NC} raven"
echo -e "  ${BLUE}•${NC} insights (v16)"
echo -e "  ${BLUE}•${NC} wiki (v16)"
echo -e "  ${BLUE}•${NC} lms (v16)"
echo -e "  ${BLUE}•${NC} drive (v16)"
echo -e "  ${BLUE}•${NC} builder (v16)"
echo -e "  ${BLUE}•${NC} print_designer"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Start development server: ${BLUE}bench start${NC}"
echo -e "  2. Access site at: ${BLUE}http://$SITE_NAME:8000${NC}"
echo -e "  3. Run Phase 2 script for industry verticals"
echo -e "  4. Run Phase 3 script for RICCO custom apps"
echo ""
echo -e "Bench location: ${BLUE}$BENCH_PATH${NC}"
echo ""
