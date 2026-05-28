#!/bin/bash
# ============================================================================
# RICCO ERP - Frappe v16 Migration Script (Phase 2 & 3)
# Industry Verticals + RICCO Custom Apps
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BENCH_PATH="/home/z/my-project/frappe-bench-v16"
SITE_NAME="ricco-dev.local"

cd "$BENCH_PATH" 2>/dev/null || {
    echo -e "${RED}Error: Bench not found at $BENCH_PATH${NC}"
    echo "Please run migrate-to-v16.sh first"
    exit 1
}

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  RICCO ERP Migration - Phase 2 & 3${NC}"
echo -e "${BLUE}  Industry Verticals + RICCO Apps${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Phase 2: Industry Verticals
echo -e "${YELLOW}[Phase 2] Installing industry vertical applications...${NC}"

# Healthcare (Marley)
echo -e "  ${BLUE}→${NC} Installing Healthcare (Marley HIS)..."
bench get-app https://github.com/earthians/marley healthcare || true
bench --site "$SITE_NAME" install-app healthcare 2>/dev/null || echo "  ${YELLOW}!${NC} Healthcare may need manual installation"

# Hospitality
echo -e "  ${BLUE}→${NC} Installing Hospitality..."
bench get-app hospitality --branch version-16 || true
bench --site "$SITE_NAME" install-app hospitality 2>/dev/null || echo "  ${YELLOW}!${NC} Hospitality may need manual installation"

# Agriculture
echo -e "  ${BLUE}→${NC} Installing Agriculture..."
bench get-app agriculture --branch version-16 || true
bench --site "$SITE_NAME" install-app agriculture 2>/dev/null || echo "  ${YELLOW}!${NC} Agriculture may need manual installation"

# Cargo Management
echo -e "  ${BLUE}→${NC} Installing Cargo Management..."
bench get-app https://github.com/AgileShift/cargo_management || true
bench --site "$SITE_NAME" install-app cargo_management 2>/dev/null || echo "  ${YELLOW}!${NC} Cargo management may need manual installation"

# Fleet Management
echo -e "  ${BLUE}→${NC} Installing Fleet Management..."
bench get-app https://github.com/aakvatech/transport fleet_management || true
bench --site "$SITE_NAME" install-app trans_ms 2>/dev/null || echo "  ${YELLOW}!${NC} Fleet management may need manual installation"

# Warehouse Management
echo -e "  ${BLUE}→${NC} Installing Warehouse Management..."
bench get-app https://github.com/f-9t9it/WMS warehouse_management || true
bench --site "$SITE_NAME" install-app wms 2>/dev/null || echo "  ${YELLOW}!${NC} WMS may need manual installation"

# Property Management
echo -e "  ${BLUE}→${NC} Installing Property Management..."
bench get-app https://github.com/aakvatech/PropMS property_management || true
bench --site "$SITE_NAME" install-app propms 2>/dev/null || echo "  ${YELLOW}!${NC} Property management may need manual installation"

# Utility Billing
echo -e "  ${BLUE}→${NC} Installing Utility Billing..."
bench get-app https://github.com/navariltd/utility-billing || true
bench --site "$SITE_NAME" install-app utility_billing 2>/dev/null || echo "  ${YELLOW}!${NC} Utility billing may need manual installation"

# Gym Management
echo -e "  ${BLUE}→${NC} Installing Gym Management..."
bench get-app https://github.com/anwarpatelnoori/Gym-Management-System gym_management || true
bench --site "$SITE_NAME" install-app gym_management 2>/dev/null || echo "  ${YELLOW}!${NC} Gym management may need manual installation"

# Appointment Booking
echo -e "  ${BLUE}→${NC} Installing Appointment Booking..."
bench get-app https://github.com/rtCamp/frappe-appointment appointment_booking || true
bench --site "$SITE_NAME" install-app frappe_appointment 2>/dev/null || echo "  ${YELLOW}!${NC} Appointment booking may need manual installation"

# Telephony
echo -e "  ${BLUE}→${NC} Installing Telephony..."
bench get-app telephony --branch main || true
bench --site "$SITE_NAME" install-app telephony 2>/dev/null || echo "  ${YELLOW}!${NC} Telephony may need manual installation"

# Newsletter
echo -e "  ${BLUE}→${NC} Installing Newsletter..."
bench get-app newsletter --branch main || true
bench --site "$SITE_NAME" install-app newsletter 2>/dev/null || echo "  ${YELLOW}!${NC} Newsletter may need manual installation"

# EU E-Invoice
echo -e "  ${BLUE}→${NC} Installing EU E-Invoice..."
bench get-app https://github.com/alyf-de/eu_einvoice || true
bench --site "$SITE_NAME" install-app eu_einvoice 2>/dev/null || echo "  ${YELLOW}!${NC} EU E-Invoice may need manual installation"

# Loyalty Point
echo -e "  ${BLUE}→${NC} Installing Loyalty Point..."
bench get-app https://github.com/BayuP/loyalty-point || true
bench --site "$SITE_NAME" install-app loyalty_point 2>/dev/null || echo "  ${YELLOW}!${NC} Loyalty point may need manual installation"

# Non-Profit
echo -e "  ${BLUE}→${NC} Installing Non-Profit..."
bench get-app non_profit --branch version-16 || true
bench --site "$SITE_NAME" install-app non_profit 2>/dev/null || echo "  ${YELLOW}!${NC} Non-profit may need manual installation"

# Frappe Studio
echo -e "  ${BLUE}→${NC} Installing Frappe Studio..."
bench get-app https://github.com/frappe/studio frappe_studio || true
bench --site "$SITE_NAME" install-app studio 2>/dev/null || echo "  ${YELLOW}!${NC} Frappe Studio may need manual installation"

# Frappe Assets
echo -e "  ${BLUE}→${NC} Installing Frappe Assets..."
bench get-app https://github.com/frappe/assets frappe_assets || true
bench --site "$SITE_NAME" install-app assets 2>/dev/null || echo "  ${YELLOW}!${NC} Frappe Assets may need manual installation"

echo -e "  ${GREEN}✓${NC} Industry verticals installation completed"
echo ""

# Phase 3: RICCO Custom Apps
echo -e "${YELLOW}[Phase 3] Installing RICCO custom applications...${NC}"
echo -e "${YELLOW}Note: RICCO apps need to be copied from existing repository${NC}"
echo ""

# Check if RICCO apps exist
OLD_APPS="/home/z/my-project/frappe-bench/apps"

if [ -d "$OLD_APPS/ricco_theme" ]; then
    echo -e "  ${BLUE}→${NC} Copying RICCO apps from existing bench..."
    
    for app in ricco_theme ricco_pos ricco_payments ricco_whatsapp \
               ricco_woocommerce ricco_localization ricco_messaging \
               ricco_verticals ricco_ai ricco_productivity; do
        
        if [ -d "$OLD_APPS/$app" ]; then
            cp -r "$OLD_APPS/$app" "$BENCH_PATH/apps/"
            echo -e "  ${GREEN}✓${NC} Copied $app"
        else
            echo -e "  ${YELLOW}!${NC} $app not found in source"
        fi
    done
    
    # Install RICCO apps
    echo ""
    echo -e "  ${BLUE}→${NC} Installing RICCO apps to site..."
    
    bench --site "$SITE_NAME" install-app ricco_theme 2>/dev/null || echo "  ${YELLOW}!${NC} ricco_theme needs configuration"
    bench --site "$SITE_NAME" install-app ricco_pos 2>/dev/null || echo "  ${YELLOW}!${NC} ricco_pos needs configuration"
    bench --site "$SITE_NAME" install-app ricco_payments 2>/dev/null || echo "  ${YELLOW}!${NC} ricco_payments needs configuration"
    bench --site "$SITE_NAME" install-app ricco_whatsapp 2>/dev/null || echo "  ${YELLOW}!${NC} ricco_whatsapp needs configuration"
    bench --site "$SITE_NAME" install-app ricco_woocommerce 2>/dev/null || echo "  ${YELLOW}!${NC} ricco_woocommerce needs configuration"
    bench --site "$SITE_NAME" install-app ricco_localization 2>/dev/null || echo "  ${YELLOW}!${NC} ricco_localization needs configuration"
    bench --site "$SITE_NAME" install-app ricco_messaging 2>/dev/null || echo "  ${YELLOW}!${NC} ricco_messaging needs configuration"
    bench --site "$SITE_NAME" install-app ricco_verticals 2>/dev/null || echo "  ${YELLOW}!${NC} ricco_verticals needs configuration"
    bench --site "$SITE_NAME" install-app ricco_ai 2>/dev/null || echo "  ${YELLOW}!${NC} ricco_ai needs configuration"
    bench --site "$SITE_NAME" install-app ricco_productivity 2>/dev/null || echo "  ${YELLOW}!${NC} ricco_productivity needs configuration"
    
else
    echo -e "  ${YELLOW}!${NC} RICCO apps not found at $OLD_APPS"
    echo -e "  ${YELLOW}!${NC} Please provide RICCO app repository URLs"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Migration Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Start your server with: ${BLUE}bench start${NC}"
echo -e "Access at: ${BLUE}http://$SITE_NAME:8000${NC}"
echo ""
