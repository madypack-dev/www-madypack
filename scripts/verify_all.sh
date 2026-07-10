#!/bin/bash
# Script de verificación integral para Madypack.
#
# Realiza:
#   1. Ejecución de tests unitarios e integración (pytest) con validación de cobertura >= 85%.
#   2. Ejecución de la auditoría de rutas y SEO frente a producción (audit_site.py).

set -e

# Asegurar que estamos en la raíz del proyecto
DIR_BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR_BASE"

echo "============================================================"
echo " INICIANDO VERIFICACIÓN INTEGRAL DE MADYPACK"
echo "============================================================"

# 1. Ejecutar Tests y Cobertura
echo -e "\n[PASO 1] Ejecutando suite de pruebas y validando cobertura de código..."
echo "------------------------------------------------------------"
PYTHONPATH=. ./venv/bin/pytest --cov=src --cov-fail-under=85

# 2. Ejecutar Auditoría de Sitio y SEO
echo -e "\n[PASO 2] Ejecutando auditoría de rutas, SEO y fidelidad de frontend..."
echo "------------------------------------------------------------"
PYTHONPATH=. ./venv/bin/python scripts/audit_site.py

echo -e "\n============================================================"
echo " 🎉 ¡VERIFICACIÓN COMPLETADA CON ÉXITO!"
echo " Todos los tests pasaron, la cobertura es >= 85% y la"
echo " réplica del sitio superó la auditoría de fidelidad."
echo "============================================================"
exit 0
