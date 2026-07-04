#!/bin/bash
# Levanta el servidor de desarrollo para un tenant específico.
# Si el puerto está ocupado, mata el proceso que lo usa.
#
# Uso:
#   ./run.sh              # puerto 8000 -> default
#   ./run.sh 8001         # puerto 8001 -> madypack
#   ./run.sh madypack     # equivalente al anterior
#   ./run.sh empresa-2    # puerto 8002 -> empresa-2

set -e

PUERTO="${1:-8000}"

# Mapeo de nombres de tenant a puertos.
declare -A TENANT_PUERTO=(
    ["default"]="8000"
    ["madypack"]="8001"
    ["empresa-2"]="8002"
    ["empresa-3"]="8003"
    ["empresa-4"]="8004"
)

# Si el argumento es un nombre de tenant conocido, derivar el puerto.
if [[ -n "${TENANT_PUERTO[$PUERTO]:-}" ]]; then
    PUERTO="${TENANT_PUERTO[$PUERTO]}"
fi

# Validar que el puerto sea numérico.
if ! [[ "$PUERTO" =~ ^[0-9]+$ ]]; then
    echo "Uso: $0 [puerto|tenant]"
    echo "Tenants disponibles:"
    for TENANT in "${!TENANT_PUERTO[@]}"; do
        echo "  $0 $TENANT   # puerto ${TENANT_PUERTO[$TENANT]}"
    done
    exit 1
fi

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

echo "Liberando puerto $PUERTO si está ocupado..."
_liberar_puerto "$PUERTO"

echo "Iniciando servidor en puerto $PUERTO..."
./venv/bin/uvicorn src.infraestructura.app:app --port "$PUERTO" --reload
