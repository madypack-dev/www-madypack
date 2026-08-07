#!/bin/bash
# Levanta el Servidor Privado de Integración ERP (Xubio) para desarrollo local.
#
# Uso:
#   ./run_erp.sh [puerto]
#
# Puerto por defecto: 8001

set -e

PUERTO="${1:-8001}"

_liberar_puerto() {
    local PUERTO_LIBERAR="$1"
    if command -v fuser &> /dev/null; then
        fuser -k "${PUERTO_LIBERAR}/tcp" 2>/dev/null || true
    elif command -v lsof &> /dev/null; then
        local PID
        PID=$(lsof -ti ":$PUERTO_LIBERAR" 2>/dev/null || true)
        if [ -n "$PID" ]; then
            kill -9 "$PID" 2>/dev/null || true
        fi
    fi
}

echo "INFO:     Liberando puerto $PUERTO si está ocupado..."
_liberar_puerto "$PUERTO"

echo "INFO:     Iniciando Servidor Privado ERP (Xubio) en puerto $PUERTO..."
./venv/bin/uvicorn src.infrastructure.fastapi.app_integracion_erp:app_erp --port "$PUERTO" --reload
