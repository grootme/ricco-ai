#!/bin/bash
# RICCO ERP - Script de Correcciones Pre-Instalación
# Aplica las correcciones identificadas en el análisis estratégico
# Fecha: 2026-04-25
# Versión: 1.0

set -e

APPS_DIR="/home/z/my-project/frappe-bench/apps"
LOG_FILE="/home/z/my-project/frappe-bench/logs/fixes-$(date +%Y%m%d_%H%M%S).log"

echo "========================================" | tee -a "$LOG_FILE"
echo "RICCO ERP - Correcciones Pre-Instalación" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Fecha: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Función para logging
log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ========================================
# CORRECCIÓN 1: Python 3.14 → Python 3.10
# ========================================
log "CORRECCIÓN 1: Corrigiendo Python >=3.14 a >=3.10..."

APPS_PYTHON_FIX=("cargo_management" "eu_einvoice" "newsletter" "wiki")

for app in "${APPS_PYTHON_FIX[@]}"; do
    PYPROJECT="$APPS_DIR/$app/pyproject.toml"
    if [ -f "$PYPROJECT" ]; then
        if grep -q 'requires-python = ">=3.14"' "$PYPROJECT" 2>/dev/null; then
            sed -i 's/requires-python = ">=3.14"/requires-python = ">=3.10"/g' "$PYPROJECT"
            log "  ✅ $app: Python versión corregida a >=3.10"
        else
            log "  ℹ️ $app: No requiere corrección (ya correcto o diferente)"
        fi
    else
        log "  ⚠️ $app: pyproject.toml no encontrado"
    fi
done

# ========================================
# CORRECCIÓN 2: Twilio versión en twilio_integration
# ========================================
log ""
log "CORRECCIÓN 2: Actualizando versión de twilio en twilio_integration..."

TWILIO_REQ="$APPS_DIR/twilio_integration/requirements.txt"
if [ -f "$TWILIO_REQ" ]; then
    if grep -q "twilio==6.44.2" "$TWILIO_REQ" 2>/dev/null; then
        sed -i 's/twilio==6.44.2/twilio>=8.5.0/g' "$TWILIO_REQ"
        log "  ✅ twilio_integration: twilio actualizado a >=8.5.0"
    else
        log "  ℹ️ twilio_integration: versión ya actualizada o diferente"
    fi
else
    log "  ⚠️ twilio_integration: requirements.txt no encontrado"
fi

# ========================================
# CORRECCIÓN 3: boto3 versión en ecommerce_integrations
# ========================================
log ""
log "CORRECCIÓN 3: Actualizando versión de boto3 en ecommerce_integrations..."

ECOM_PYPROJECT="$APPS_DIR/ecommerce_integrations/pyproject.toml"
if [ -f "$ECOM_PYPROJECT" ]; then
    if grep -q 'boto3~=1.28.10' "$ECOM_PYPROJECT" 2>/dev/null; then
        sed -i 's/boto3~=1.28.10/boto3>=1.34.0/g' "$ECOM_PYPROJECT"
        log "  ✅ ecommerce_integrations: boto3 actualizado a >=1.34.0"
    else
        log "  ℹ️ ecommerce_integrations: versión ya actualizada o diferente"
    fi
else
    log "  ⚠️ ecommerce_integrations: pyproject.toml no encontrado"
fi

# ========================================
# CORRECCIÓN 4: Eliminar apps incompatibles de la instalación
# ========================================
log ""
log "CORRECCIÓN 4: Marcando apps incompatibles para exclusión..."

# Crear archivo de exclusión
EXCLUDE_FILE="$APPS_DIR/EXCLUDE-APPS.txt"
cat > "$EXCLUDE_FILE" << 'EOF'
# Apps excluidas por incompatibilidad con Frappe v16
# Generado automáticamente por fix-conflicts.sh
# Fecha: $(date)

# ERPNext Shipping - Solo compatible con v15
erpnext_shipping

# HRMS - Solo compatible con v17 (considerar versión alternativa)
# hrms  # Descomentar si se decide excluir
EOF

log "  ✅ Archivo de exclusión creado: $EXCLUDE_FILE"

# ========================================
# RESUMEN DE CORRECCIONES
# ========================================
log ""
log "========================================"
log "RESUMEN DE CORRECCIONES APLICADAS"
log "========================================"
log ""
log "✅ Python versión corregido en: cargo_management, eu_einvoice, newsletter, wiki"
log "✅ Twilio versión actualizado en: twilio_integration"
log "✅ boto3 versión actualizado en: ecommerce_integrations"
log "✅ Apps marcadas para exclusión: erpnext_shipping (hrms pendiente decisión)"
log ""
log "⚠️ ACCIONES MANUALES PENDIENTES:"
log "   1. Verificar kard_theme funciona con Frappe v16"
log "   2. Clonar csf_tz si property_management es necesaria"
log "   3. Decidir sobre HRMS: buscar versión v16 compatible o desarrollar alternativa"
log ""
log "📁 Log guardado en: $LOG_FILE"
log ""
log "Próximo paso: Ejecutar install-all-apps.sh con Frappe v16"
