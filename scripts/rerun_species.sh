#!/usr/bin/env bash
# Rerun every revision run set for ONE species after its input file changed,
# split into one process per m (or per radius x m, per feature string) so it
# finishes quickly. Seeds depend only on the repeat index, so the split gives
# the same fits as the combined launch. Old results of that species are deleted.
# Usage: bash scripts/rerun_species.sh Root_Weevil
set -euo pipefail
SP="$1"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/.venv/bin/python"
export MAXENT_DATA_ROOT="${ROOT}/data" MPLBACKEND=Agg PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1
COMMON=(--pathways SSP_245 --insects "${SP}" --background-count 10000 --thin-distance 10000 --corr-include-elevation --feature-types lph)
mkdir -p "${ROOT}/logs"
for set in revision_main revision_swap revision_radius80 revision_radius320 revision_grid revision_percell; do
    rm -rf "${ROOT}/runs/${set}/SSP_245/${SP}"
done
rm -rf "${ROOT}/runs/revision_gcm/${SP}"
go() { local root="$1" log="$2"; shift 2; MAXENT_RESULTS_ROOT="${ROOT}/runs/${root}" nohup "${PY}" -m maxent_insect_dir.run "$@" >"${ROOT}/logs/${log}.log" 2>&1 & }
for m in 0 0.25 0.5 0.75 1; do
    go revision_main "rerun_${SP}_main_m${m}" "${COMMON[@]}" --beta-multipliers 2.0 --bias-mix "$m" --repeats 20 --seed 1000 --project-pathways SSP_126 SSP_245 SSP_370 SSP_585
    go revision_swap "rerun_${SP}_swap_m${m}" "${COMMON[@]}" --beta-multipliers 2.0 --bias-mix "$m" --repeats 20 --seed 1000 --swap-folds --skip-projections
done
for r in 80 320; do for m in 0.25 0.5 0.75; do
    go "revision_radius${r}" "rerun_${SP}_radius${r}_m${m}" "${COMMON[@]}" --beta-multipliers 2.0 --bias-mix "$m" --repeats 10 --seed 1000 --kernel-radius "${r}000" --skip-projections
done; done
for f in l lq lqh lph lqhp lqhpt; do
    MAXENT_RESULTS_ROOT="${ROOT}/runs/revision_grid" nohup "${PY}" -m maxent_insect_dir.run --pathways SSP_245 --insects "${SP}" \
        --background-count 10000 --thin-distance 10000 --corr-include-elevation --feature-types "$f" \
        --beta-multipliers 0.5 1.0 1.5 2.0 2.5 --bias-mix 0.25 --repeats 4 --seed 2000 \
        --project-pathways SSP_126 SSP_245 SSP_370 SSP_585 >"${ROOT}/logs/rerun_${SP}_grid_${f}.log" 2>&1 &
done
go revision_percell "rerun_${SP}_percell" "${COMMON[@]}" --beta-multipliers 2.0 --bias-mix 0.25 --repeats 20 --seed 1000 --thin-one-per-cell
echo "launched $(jobs -p | wc -l) processes for ${SP}"
