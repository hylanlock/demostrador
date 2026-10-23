#!/usr/bin/env bash
# Prepara el demostrador en el móvil (Ubuntu dentro de Termux). Ejecutar desde la carpeta del demostrador:
#     bash instalar-movil.sh
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Instalando python3 y git..."
  apt-get update && apt-get install -y python3 git
fi
python3 -c 'import sys; assert sys.version_info >= (3, 9), "Hace falta Python 3.9 o superior"'

if [ -d hylanlock/.git ]; then
  echo "Actualizando Hylanlock..."
  git -C hylanlock pull --ff-only
elif [ ! -d ../hylanlock/app ]; then
  echo "Descargando Hylanlock..."
  git clone https://github.com/hylanlock/hylanlock
fi

mkdir -p licencias datos
if [ ! -f licencias/hylanlock.license.key ]; then
  echo
  echo "FALTA la licencia de demo. Genérala en el PC (carpeta hylanlock):"
  echo '    python tools/license_gen.py -c "Demo Nicolas" -t commercial --expires 2027-12-31 -o demo'
  echo "y copia el contenido del .txt a:  $(pwd)/licencias/hylanlock.license.key"
fi

echo
echo "Listo. Arranca con:   python3 demostrador.py"
echo "y abre en el navegador del móvil:   http://127.0.0.1:8088"
