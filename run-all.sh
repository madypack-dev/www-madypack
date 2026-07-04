#!/bin/bash
# Levanta todas las empresas configuradas en paralelo para desarrollo local.
#
# Uso:
#   ./run-all.sh
#
# Para detener todas las instancias, presioná Ctrl+C.

set -e

PUERTOS=(8000 8001)
PIDS=()

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
    echo "Iniciando servidor en puerto $PUERTO..."
    ./venv/bin/uvicorn src.infraestructura.app:app --port "$PUERTO" --reload &
    PIDS+=("$!")
done

echo "Servidores corriendo en puertos: ${PUERTOS[*]}"
echo "Presioná Ctrl+C para detenerlos."
wait
