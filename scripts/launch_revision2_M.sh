#!/usr/bin/env bash
# Revision 2 (accessible area): repeat the background-sampling experiment
# inside species-specific accessible areas M. One process per species and M
# definition; each runs m = 0, 0.25, 0.5, 0.75, 1 with 20 seeded repeats
# (seeds 1000-1019, the same as the main set) and the SSP2-4.5 projection.
# Masks: data/data/accessible_area/<Species>_<def>.tif (scripts/accessible_area.py).
# Usage: bash scripts/launch_revision2_M.sh [eco eco100 rec200]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/.venv/bin/python"
export MAXENT_DATA_ROOT="${ROOT}/data" MPLBACKEND=Agg PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1
DEFS=("$@"); [ ${#DEFS[@]} -eq 0 ] && DEFS=(eco eco100 rec200)
mkdir -p "${ROOT}/logs"
for d in "${DEFS[@]}"; do
  for sp in Brown_Marmorated_Stink_bug Corn_Earworm Spongy_Moth Root_Weevil Spotted_Lanternfly; do
    MAXENT_RESULTS_ROOT="${ROOT}/runs/revision2_M_${d}" nohup "${PY}" -m maxent_insect_dir.run \
      --pathways SSP_245 --insects "${sp}" --background-count 10000 --thin-distance 10000 \
      --corr-include-elevation --feature-types lph --beta-multipliers 2.0 \
      --bias-mix 0 0.25 0.5 0.75 1 --repeats 20 --seed 1000 --accessible-area "${d}" \
      > "${ROOT}/logs/revision2_M_${d}_${sp}.log" 2>&1 &
  done
done
echo "launched $(jobs -p | wc -l) processes"
