#!/usr/bin/env bash
# Create .venv at the repo root and install elapid plus this package.
# If the existing venv already imports both, leave it alone.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${ROOT}/.venv"
PY="${VENV}/bin/python"
ELAPID="$(cd "${ROOT}/../elapid/elapid" && pwd)"
PKG="${ROOT}/MaxEnt_insect_dir"

if [[ -x "${PY}" ]] && "${PY}" -c "import elapid, geopandas, rasterio, maxent_insect_dir" >/dev/null 2>&1; then
    echo "venv ready: ${PY}"
    "${PY}" -c "import elapid, maxent_insect_dir; print('elapid', elapid.__file__); print('maxent', maxent_insect_dir.__file__)"
    exit 0
fi

python3 -m venv "${VENV}"
"${VENV}/bin/pip" install -U pip
"${VENV}/bin/pip" install -e "${ELAPID}"
"${VENV}/bin/pip" install -e "${PKG}[dev]"
echo "venv created: ${PY}"
