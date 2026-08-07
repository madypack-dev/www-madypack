#!/bin/bash
# Levanta de forma simultánea el Servidor Público Web (8000) y el Servidor Privado ERP (8001).
#
# Uso:
#   ./run_all.sh

set -e

echo "INFO:     Iniciando Servidor Privado ERP (8001) y Servidor Público Web (8000)..."

./run_erp.sh 8001 &
PID_ERP=$!

./run_web.sh 8000 &
PID_WEB=$!

trap "kill $PID_ERP $PID_WEB 2>/dev/null || true" EXIT

wait $PID_ERP $PID_WEB
