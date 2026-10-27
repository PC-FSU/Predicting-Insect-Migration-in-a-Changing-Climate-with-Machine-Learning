#!/usr/bin/env bash
# Rerun the manuscript performance table: CBI and AUC versus mixing coefficient.
# Five species run at once. Each species is 5 values of m x 20 repeats.
# Projections are skipped; the table only needs the fit metrics.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT}/.venv/bin/python"
export MAXENT_DATA_ROOT="${ROOT}/data"
export MAXENT_RESULTS_ROOT="${ROOT}/runs/paper_m_table"
export MPLBACKEND=Agg
export PYTHONUNBUFFERED=1

mkdir -p "${ROOT}/logs" "${MAXENT_RESULTS_ROOT}"

if [[ ! -x "${PY}" ]]; then
    echo "No venv at ${PY}. Run: bash ${ROOT}/scripts/setup_venv.sh" >&2
    exit 1
fi

INSECTS=(
    Brown_Marmorated_Stink_bug
    Corn_Earworm
    Root_Weevil
    Spongy_Moth
    Spotted_Lanternfly
)

pids=()
for insect in "${INSECTS[@]}"; do
    log="${ROOT}/logs/paper_m_table_${insect}.log"
    echo "starting ${insect} -> ${log}"
    "${PY}" -m maxent_insect_dir.run \
        --pathways SSP_245 \
        --insects "${insect}" \
        --feature-types lph \
        --beta-multipliers 2.0 \
        --bias-mix 0 0.25 0.5 0.75 1 \
        --repeats 20 \
        --background-count 10000 \
        --skip-projections \
        >"${log}" 2>&1 &
    pids+=("$!")
done

fail=0
for pid in "${pids[@]}"; do
    if ! wait "${pid}"; then
        fail=1
    fi
done

if [[ "${fail}" -ne 0 ]]; then
    echo "one or more species failed; see ${ROOT}/logs/paper_m_table_*.log" >&2
    exit 1
fi

echo "finished. summarize with: ${PY} ${ROOT}/scripts/summarize_m_table.py"
