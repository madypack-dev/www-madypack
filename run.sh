#!/bin/bash
# Script ejecutable principal de compatibilidad.
# Redirige la ejecución a ./run_web.sh (Servidor Público Web).

set -e

exec ./run_web.sh "$@"
