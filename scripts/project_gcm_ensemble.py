#!/usr/bin/env python3
"""Project saved models onto the future layers of several GCMs (fit once, project everywhere).

For every experiment_states.pkl of one species (one m, feature and beta) under
--results, the fitted elapid model is applied to the clipped bioclim layers of
each GCM, SSP and period. ACCESS-CM2 comes from the study's own layers
(config.config_worldclim); the other GCMs from data/data/GCM_ensemble/<GCM>/ssp<N>/<period>/Clipped/In_tiff_format
(scripts/prepare_gcm_layers.py). Elevation is the same raster everywhere.

Output: runs/revision_gcm/<species>/<run folder name>/<GCM>_ssp<N>_<period>.tif

Usage:
    python scripts/project_gcm_ensemble.py --species Brown_Marmorated_Stink_bug \
        --results runs/revision_main --out runs/revision_gcm
"""

from __future__ import annotations

import argparse
import glob
import os
import time
from pathlib import Path

import elapid as ela
import joblib

from maxent_insect_dir import config

os.environ.setdefault("MPLBACKEND", "Agg")
ROOT = Path(__file__).resolve().parents[1]
PERIODS = ["2021_2040", "2041_2060"]
SSPS = ["126", "245", "370", "585"]


def layer_dir(gcm: str, ssp: str, period: str, gcm_root: Path) -> Path:
    if gcm == "ACCESS-CM2":
        return Path(config.config_worldclim[f"SSP_{ssp}"][period])
    return gcm_root / gcm / f"ssp{ssp}" / period / "Clipped" / "In_tiff_format"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--species", required=True)
    ap.add_argument("--results", default="runs/revision_main")
    ap.add_argument("--pathway", default="SSP_245")
    ap.add_argument("--m", default="0.25")
    ap.add_argument("--feature", default="lph")
    ap.add_argument("--beta", default="2.0")
    ap.add_argument("--gcms", nargs="+", default=["MPI-ESM1-2-HR", "MIROC6", "UKESM1-0-LL", "EC-Earth3-Veg"])
    ap.add_argument("--gcm-root", default=str(ROOT / "data/data/GCM_ensemble"))
    ap.add_argument("--out", default="runs/revision_gcm")
    args = ap.parse_args()

    states = sorted(glob.glob(f"{args.results}/{args.pathway}/{args.species}/{args.m}/{args.feature}/{args.beta}/*/experiment_states.pkl"))
    if not states:
        raise SystemExit("no states found")
    t0 = time.time(); n = 0
    for sp in states:
        s = joblib.load(sp)
        model, cols = s["model"], list(s["x_train"].columns)
        del s
        out_dir = Path(args.out) / args.species / Path(sp).parent.name
        out_dir.mkdir(parents=True, exist_ok=True)
        for gcm in args.gcms:
            for ssp in SSPS:
                for period in PERIODS:
                    out = out_dir / f"{gcm}_ssp{ssp}_{period}.tif"
                    if out.exists():
                        continue
                    d = layer_dir(gcm, ssp, period, Path(args.gcm_root))
                    if not (d / "Bio1.tif").exists():
                        print("missing layers:", d); continue
                    rasters = [str(config.PATH_TO_ELEVATION_DATA) if c == "elevation" else str(d / f"{c}.tif") for c in cols]
                    ela.apply_model_to_rasters(model, rasters, str(out), quiet=True)
                    n += 1
        print(f"{Path(sp).parent.name}: done ({n} rasters, {time.time()-t0:.0f}s)", flush=True)
    print("finished", n, "rasters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
