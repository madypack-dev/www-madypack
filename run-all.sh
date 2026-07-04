#!/bin/bash
# Levanta todas las empresas configuradas en paralelo para desarrollo local.
# Libera los puertos antes de levantar cada instancia.
#
# Uso:
#   ./run-all.sh
#
# Para detener todas las instancias, presioná Ctrl+C.

set -e

PUERTOS=(8000 8001)
PIDS=()

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

cleanup() {
    echo ""
    echo "Deteniendo servidores..."
    for PID in "${PIDS[@]}"; do
        kill "$PID" 2>/dev/null || true
    done
    wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

for PUERTO in "${PUERTOS[@]}"; do
    echo "Liberando puerto $PUERTO si está ocupado..."
    _liberar_puerto "$PUERTO"
done

for PUERTO in "${PUERTOS[@]}"; do
    echo "Iniciando servidor en puerto $PUERTO..."
    ./venv/bin/uvicorn src.infraestructura.app:app --port "$PUERTO" --reload &
    PIDS+=("$!")
done

echo "Servidores corriendo en puertos: ${PUERTOS[*]}"
echo "Presioná Ctrl+C para detenerlos."
wait
