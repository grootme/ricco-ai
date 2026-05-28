#!/bin/bash
# =============================================================================
# RICCO AI - Stop All Services Script
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/home/z/my-project"

echo -e "${BLUE}=============================================================${NC}"
echo -e "${BLUE}        RICCO AI - Stopping All Services                     ${NC}"
echo -e "${BLUE}=============================================================${NC}"

# Stop application processes
echo -e "${YELLOW}Stopping application processes...${NC}"
pkill -f "uvicorn src.main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "mcp_proxy" 2>/dev/null || true

# Stop Docker containers
echo -e "${YELLOW}Stopping Docker containers...${NC}"
cd "$PROJECT_ROOT"

# Stop monitoring stack
docker-compose -f docker-compose-monitoring.yml down 2>/dev/null || true

# Stop main services
docker-compose down 2>/dev/null || true

# Clean up PID files
rm -f /tmp/ricco_backend.pid
rm -f /tmp/ricco_frontend.pid

echo -e "${GREEN}=============================================================${NC}"
echo -e "${GREEN}           All Services Stopped                              ${NC}"
echo -e "${GREEN}=============================================================${NC}"
