#!/usr/bin/env bash
set -eo pipefail

COLOR_RESET="\033[0m"
COLOR_INFO="\033[1;34m"
COLOR_SUCCESS="\033[1;32m"
COLOR_WARN="\033[1;33m"

log_stage() {
    echo -e "\n${COLOR_INFO}🛡️  [CI - UNCLE BOB GAUNTLET] $1${COLOR_RESET}"
}

PYTHON_BIN="./venv/bin/python"
RUFF_BIN="./venv/bin/ruff"
MYPY_BIN="./venv/bin/mypy"
VULTURE_BIN="./venv/bin/vulture"
BANDIT_BIN="./venv/bin/bandit"
PYTEST_BIN="./venv/bin/pytest"
MUTMUT_BIN="./venv/bin/mutmut"

# 0. Compilar CSS bundle
log_stage "Paso 0: Compilando CSS Bundle..."
$PYTHON_BIN -m src.infrastructure.tailwindcss.css_bundle

# 1. Clean Architecture Guard
log_stage "Paso 1: Verificando Reglas de Arquitectura Limpia (AST Import Checker y Read-Only Xubio)..."
$PYTHON_BIN scripts/check_clean_architecture.py
$PYTHON_BIN scripts/check_xubio_read_only.py

# 2. Formatting, Linting y Complejidad Ciclomática (Ruff + McCabe <= 7)
log_stage "Paso 2: Verificando Estilo y Complejidad (Ruff)..."
$RUFF_BIN check src/ tests/

# 3. Análisis Estático de Tipos (Mypy)
log_stage "Paso 3: Verificando Tipos Estáticos en Dominio y Aplicación (Mypy)..."
$MYPY_BIN src/domain src/application

# 4. Código Muerto & Auditoría de Seguridad
log_stage "Paso 4: Auditoría de Seguridad (Bandit) y Código Muerto (Vulture)..."
$BANDIT_BIN -q -r src/ -s B110,B603,B607,B404
$VULTURE_BIN src/ --min-confidence 80

# 5. Suite de Tests Unitarios + BDD Gherkin con Cobertura
log_stage "Paso 5: Pruebas Unitarias, BDD Gherkin y Cobertura..."
$PYTEST_BIN --cov-fail-under=85

# 6. Pruebas de Mutación (Mutmut)
if [ "$1" == "--fast" ]; then
    echo -e "${COLOR_WARN}⏩ Omisión de Mutation Testing (--fast activado)${COLOR_RESET}"
else
    log_stage "Paso 6: Mutation Testing en Capa de Dominio (Mutmut)..."
    rm -rf mutants
    mkdir -p mutants
    ln -sfn ../templates mutants/templates
    trap 'rm -f mutants/templates' EXIT
    $MUTMUT_BIN run
fi

echo -e "\n${COLOR_SUCCESS}👑 ¡CÓDIGO PERFECTO! El gauntlet del Tío Bob fue superado exitosamente.${COLOR_RESET}\n"
