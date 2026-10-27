#!/usr/bin/env bash
# Download WorldClim 2.1 CMIP6 10-arcmin bioclimatic layers for extra GCMs.
# Used to separate climate-model spread from background-sampling spread.
# The original study used ACCESS-CM2 only (already under data/data/SSP_*).
# Files land in data/data/GCM_ensemble/<GCM>/ssp<N>/ (gitignored, ~35 MB each).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DST="${ROOT}/data/data/GCM_ensemble"
GCMS=(${GCMS:-MPI-ESM1-2-HR MIROC6 UKESM1-0-LL EC-Earth3-Veg})
SSPS=(126 245 370 585)
PERIODS=(2021-2040 2041-2060)
for g in "${GCMS[@]}"; do for s in "${SSPS[@]}"; do for p in "${PERIODS[@]}"; do
  d="${DST}/${g}/ssp${s}"; mkdir -p "$d"
  f="wc2.1_10m_bioc_${g}_ssp${s}_${p}.tif"
  if [[ -s "$d/$f" ]]; then echo "have $f"; continue; fi
  echo "get  $f"
  curl -sS -m 900 -L --retry 3 --retry-delay 10 -C - -o "$d/$f.part" \
    "https://geodata.ucdavis.edu/cmip6/10m/${g}/ssp${s}/${f}" && mv "$d/$f.part" "$d/$f" || echo "FAILED $f"
done; done; done
echo "done: $(find "$DST" -name '*.tif' | wc -l) files"
