#!/bin/bash
# Levanta el servidor de desarrollo para un tenant específico.
# Si el puerto está ocupado, mata el proceso que lo usa.
#
# Uso:
#   ./run.sh              # puerto 8000 -> default
#   ./run.sh 8001         # puerto 8001 -> madypack
#   ./run.sh madypack     # equivalente al anterior
#   ./run.sh eitec        # puerto 8002 -> eitec

set -e

PUERTO="${1:-8000}"

# Si el argumento es un nombre de tenant conocido, derivar el puerto desde settings.
if ./venv/bin/python -c "from src.infraestructura.config import MAPEO_TENANT_PUERTO; exit(0 if '$PUERTO' in MAPEO_TENANT_PUERTO else 1)" 2>/dev/null; then
    PUERTO=$(./venv/bin/python -c "from src.infraestructura.config import MAPEO_TENANT_PUERTO; print(MAPEO_TENANT_PUERTO['$PUERTO'])")
fi

# Validar que el puerto sea numérico.
if ! [[ "$PUERTO" =~ ^[0-9]+$ ]]; then
    echo "Uso: $0 [puerto|tenant]"
    echo "Tenants disponibles:"
    ./venv/bin/python -c "from src.infraestructura.config import MAPEO_TENANT_PUERTO; [print(f'  $0 {t}   # puerto {p}') for t, p in MAPEO_TENANT_PUERTO.items()]"
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
