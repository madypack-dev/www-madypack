#!/bin/bash
# Levanta la aplicación Madypack para desarrollo local.
#
# Uso:
#   ./run.sh [puerto]
#
# Puerto por defecto: 8000

set -e

PUERTO="${1:-8000}"

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

echo "INFO:     Iniciando servidor Madypack en puerto $PUERTO..."
./venv/bin/uvicorn src.infraestructura.app:app --port "$PUERTO" --reload
