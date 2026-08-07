#!/bin/bash
# Levanta el Servidor Público Web (Madypack Ecommerce) para desarrollo local.
#
# Uso:
#   ./run_web.sh [puerto]
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

echo "INFO:     Compilando bundle CSS..."
./venv/bin/python -m src.infrastructure.tailwindcss.css_bundle

echo "INFO:     Iniciando Servidor Público Web en puerto $PUERTO..."
./venv/bin/uvicorn src.infrastructure.fastapi.app_web_publica:app_web --port "$PUERTO" --reload
