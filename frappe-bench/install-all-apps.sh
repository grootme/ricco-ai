#!/bin/bash
# RICCO ERP - Instalación Masiva de Apps v3.0
# Fecha: 2026-04-25
# Total Apps: 47 (22 oficiales + 15 terceros + 10 RICCO)
# Compatible con: Frappe 15.x + ERPNext 15.x

set -e

BENCH_DIR="/home/z/my-project/frappe-bench"
SITE_NAME="${1:-erpnext.local}"

echo "========================================"
echo "RICCO ERP - Instalación Masiva v3.0"
echo "========================================"
echo "Site: $SITE_NAME"
echo "Bench Directory: $BENCH_DIR"
echo "Total Apps: 47"
echo ""

cd "$BENCH_DIR"

# Función para instalar app
install_app() {
    local app_name=$1
    echo ""
    echo ">>> Instalando: $app_name"
    if bench --site "$SITE_NAME" install-app "$app_name" 2>&1; then
        echo "✅ $app_name instalado correctamente"
    else
        echo "⚠️ Error instalando $app_name - continuando..."
    fi
}

# Verificar que el site existe
echo "Verificando site: $SITE_NAME"
if ! bench site-list | grep -q "$SITE_NAME"; then
    echo "❌ El site $SITE_NAME no existe"
    echo "Creando site nuevo..."
    bench new-site "$SITE_NAME" --admin-password admin --mariadb-root-password admin
fi

echo ""
echo "========================================"
echo "FASE 1: Core ERP (4 apps)"
echo "========================================"
install_app "hrms"
install_app "payments"
install_app "crm"
install_app "helpdesk"

echo ""
echo "========================================"
echo "FASE 2: E-Commerce & POS (6 apps)"
echo "========================================"
install_app "webshop"
install_app "ecommerce_integrations"
install_app "woocommerceconnector"
install_app "posnext"
install_app "erpnext_restaurant"
install_app "getpos"

echo ""
echo "========================================"
echo "FASE 3: Logistics & Operations (4 apps)"
echo "========================================"
install_app "erpnext_shipping"
install_app "cargo_management"
install_app "fleet_management"
install_app "warehouse_management"

echo ""
echo "========================================"
echo "FASE 4: Industry Verticals (6 apps)"
echo "========================================"
install_app "healthcare"
install_app "gym_management"
install_app "hospitality"
install_app "property_management"
install_app "utility_billing"
install_app "agriculture"

echo ""
echo "========================================"
echo "FASE 5: Finance & Billing (4 apps)"
echo "========================================"
install_app "lending"
install_app "eu_einvoice"
install_app "loyalty_point"
install_app "appointment_booking"

echo ""
echo "========================================"
echo "FASE 6: Communication (5 apps)"
echo "========================================"
install_app "raven"
install_app "telephony"
install_app "twilio_integration"
install_app "clefincode_chat"
install_app "newsletter"

echo ""
echo "========================================"
echo "FASE 7: Analytics & Knowledge (4 apps)"
echo "========================================"
install_app "insights"
install_app "wiki"
install_app "lms"
install_app "drive"

echo ""
echo "========================================"
echo "FASE 8: Design & Development (4 apps)"
echo "========================================"
install_app "builder"
install_app "print_designer"
install_app "frappe_studio"
install_app "frappe_assets"

echo ""
echo "========================================"
echo "FASE 9: RICCO Custom Apps (10 apps)"
echo "========================================"
install_app "ricco_theme"
install_app "ricco_pos"
install_app "ricco_payments"
install_app "ricco_whatsapp"
install_app "ricco_woocommerce"
install_app "ricco_localization"
install_app "ricco_messaging"
install_app "ricco_verticals"
install_app "ricco_ai"
install_app "ricco_productivity"

echo ""
echo "========================================"
echo "Migración y Reinicio"
echo "========================================"

bench --site "$SITE_NAME" migrate
bench --site "$SITE_NAME" clear-cache
bench restart

echo ""
echo "========================================"
echo "INSTALACIÓN COMPLETADA"
echo "========================================"
echo ""
echo "Apps instaladas en site: $SITE_NAME"
bench --site "$SITE_NAME" list-apps

echo ""
echo "Para iniciar el servidor:"
echo "  cd $BENCH_DIR && bench start"
echo ""
echo "Para acceder:"
echo "  URL: http://localhost:8000"
echo "  Usuario: Administrator"
echo "  Contraseña: admin"
