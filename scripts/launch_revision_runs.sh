#!/usr/bin/env bash
# Launch the run sets behind the Oct 2026 revision. Each set runs the five
# species as five background processes; logs go to logs/<set>_<species>.log.
# Usage: bash scripts/launch_revision_runs.sh main|swap|radius|grid|sm_unthinned|allrecords|percell|all
# Every set is seeded, thins all species at 10 km, adds elevation to the
# correlation filter, and uses 10,000 background points. See docs/run_index.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/.venv/bin/python"
export MAXENT_DATA_ROOT="${ROOT}/data"
export MPLBACKEND=Agg
export PYTHONUNBUFFERED=1
# keep BLAS threads modest so ten processes share 16 cores cleanly
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
mkdir -p "${ROOT}/logs"

INSECTS=(Brown_Marmorated_Stink_bug Corn_Earworm Root_Weevil Spongy_Moth Spotted_Lanternfly)
COMMON=(--pathways SSP_245 --background-count 10000 --thin-distance 10000 --corr-include-elevation)

launch() {  # launch <set-name> <extra args...>
    local name="$1"; shift
    local root="${ROOT}/runs/${name}"
    mkdir -p "${root}"
    for insect in "${INSECTS[@]}"; do
        local log="${ROOT}/logs/${name}_${insect}.log"
        echo "starting ${name} ${insect} -> ${log}"
        MAXENT_RESULTS_ROOT="${root}" nohup "${PY}" -m maxent_insect_dir.run \
            "${COMMON[@]}" --insects "${insect}" "$@" >"${log}" 2>&1 &
    done
}

case "${1:-}" in
    main)
        # Reference set: lph, beta 2.0, m sweep, 20 seeded repeats, one fit
        # projected onto every SSP (fit once, project everywhere).
        launch revision_main --feature-types lph --beta-multipliers 2.0 \
            --bias-mix 0 0.25 0.5 0.75 1 --repeats 20 --seed 1000 \
            --project-pathways SSP_126 SSP_245 SSP_370 SSP_585 ;;
    swap)
        # Same design with the checkerboard colours exchanged (two-fold check).
        launch revision_swap --feature-types lph --beta-multipliers 2.0 \
            --bias-mix 0 0.25 0.5 0.75 1 --repeats 20 --seed 1000 \
            --swap-folds --skip-projections ;;
    radius)
        # Kernel-radius sensitivity: 80 km and 320 km (160 km is the main set).
        launch revision_radius80 --feature-types lph --beta-multipliers 2.0 \
            --bias-mix 0.25 0.5 0.75 --repeats 10 --seed 1000 \
            --kernel-radius 80000 --skip-projections
        launch revision_radius320 --feature-types lph --beta-multipliers 2.0 \
            --bias-mix 0.25 0.5 0.75 --repeats 10 --seed 1000 \
            --kernel-radius 320000 --skip-projections ;;
    grid)
        # Feature-class x beta grid at m = 0.25, selected on the baseline only;
        # projections kept so the CBI-best model can be compared with lph/2.0.
        # Two processes per species (feature groups); seeds depend only on the
        # repeat index, so the split does not change any fit.
        root="${ROOT}/runs/revision_grid"; mkdir -p "${root}"
        for insect in "${INSECTS[@]}"; do
            for group in "l lq lqh" "lph lqhp lqhpt"; do
                tag="${group// /_}"
                log="${ROOT}/logs/revision_grid_${insect}_${tag}.log"
                echo "starting revision_grid ${insect} [${group}] -> ${log}"
                # shellcheck disable=SC2086
                MAXENT_RESULTS_ROOT="${root}" nohup "${PY}" -m maxent_insect_dir.run \
                    "${COMMON[@]}" --insects "${insect}" --feature-types ${group} \
                    --beta-multipliers 0.5 1.0 1.5 2.0 2.5 --bias-mix 0.25 --repeats 4 \
                    --seed 2000 --project-pathways SSP_126 SSP_245 SSP_370 SSP_585 \
                    >"${log}" 2>&1 &
            done
        done ;;
    sm_unthinned)
        # Sensitivity: spongy moth, all 203 records (incl. Washington) and no thinning,
        # as in the first submission; everything else as in the main set; metrics only.
        local_root="${ROOT}/runs/revision_sm_unthinned"; mkdir -p "${local_root}"
        MAXENT_RESULTS_ROOT="${local_root}" nohup "${PY}" -m maxent_insect_dir.run \
            --pathways SSP_245 --background-count 10000 --corr-include-elevation \
            --insects Spongy_Moth_all --feature-types lph --beta-multipliers 2.0 \
            --bias-mix 0 0.25 0.5 0.75 1 --repeats 20 --seed 1000 --skip-projections \
            >"${ROOT}/logs/revision_sm_unthinned.log" 2>&1 &
        echo "starting revision_sm_unthinned -> logs/revision_sm_unthinned.log" ;;
    allrecords)
        # Sensitivity: spongy moth and root weevil with all records (incl. the
        # out-of-range ones), thinned at 10 km like the main set; SSP2-4.5
        # projections kept so the area change can be compared with the main set.
        local_root="${ROOT}/runs/revision_allrecords"; mkdir -p "${local_root}"
        for insect in Spongy_Moth_all Root_Weevil_all; do
            MAXENT_RESULTS_ROOT="${local_root}" nohup "${PY}" -m maxent_insect_dir.run \
                "${COMMON[@]}" --insects "${insect}" --feature-types lph --beta-multipliers 2.0 \
                --bias-mix 0 0.25 0.5 0.75 1 --repeats 20 --seed 1000 \
                >"${ROOT}/logs/revision_allrecords_${insect}.log" 2>&1 &
            echo "starting revision_allrecords ${insect}"
        done ;;
    percell)
        # Sensitivity: one record per 10 arc-min cell after 10 km thinning, for the
        # three species where many thinned records share a cell; m = 0.25 only,
        # SSP2-4.5 projections kept for the area change.
        root="${ROOT}/runs/revision_percell"; mkdir -p "${root}"
        for insect in Brown_Marmorated_Stink_bug Root_Weevil Spotted_Lanternfly; do
            MAXENT_RESULTS_ROOT="${root}" nohup "${PY}" -m maxent_insect_dir.run \
                "${COMMON[@]}" --insects "${insect}" --feature-types lph --beta-multipliers 2.0 \
                --bias-mix 0.25 --repeats 20 --seed 1000 --thin-one-per-cell \
                >"${ROOT}/logs/revision_percell_${insect}.log" 2>&1 &
            echo "starting revision_percell ${insect}"
        done ;;
    all)
        for s in main swap radius grid sm_unthinned allrecords percell; do bash "$0" "$s"; done ;;
    *)
        echo "usage: $0 main|swap|radius|grid|sm_unthinned|allrecords|percell|all" >&2; exit 2 ;;
esac
