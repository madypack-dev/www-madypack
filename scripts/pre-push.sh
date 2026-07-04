#!/bin/bash
# Pre-push hook to run tests and validate test coverage is >= 85%

set -e

echo "=========================================="
echo " Ejecutando tests y validando cobertura (min 85%) antes del push..."
echo "=========================================="

# Ejecutar pytest con cobertura mínima del 85%
PYTHONPATH=. ./venv/bin/pytest --cov=src --cov-fail-under=85

echo "=========================================="
echo " ¡Todos los tests pasaron y la cobertura es >= 85%! Continuando push..."
echo "=========================================="
exit 0
