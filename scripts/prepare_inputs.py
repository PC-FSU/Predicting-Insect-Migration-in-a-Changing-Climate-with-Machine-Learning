#!/usr/bin/env python3
"""Rebuild the derived inputs of the revision (13 Oct 2026).

1. Occurrence files without records outside the established range
   (data/data/Species_Data/Clean_Data/):
     spongy_moth_est_noWA.gpkg      spongy moth without the 71 Washington State
                                    trap detections (eradicated introductions)
     Root_Weevil_est_EPPO.gpkg      Diaprepes root weevil, records from the states
                                    where EPPO lists the species as present
                                    (Florida, Texas, California, Louisiana)
2. Elevation on the climate grid (data/data/Elevation/wc2.1_10m_elev_clipped.tif):
   WorldClim 2.1 10 arc-min elevation in metres, cropped to the study window and
   masked with the land mask of the 1970-2000 baseline climate layers, so that
   every record with baseline climate data keeps an elevation value. (Future
   layers have 221 fewer coastal cells; the area comparisons are restricted to
   cells valid in both periods by scripts/analyze_projections.py.)

The WorldClim elevation zip is downloaded if it is not present.

Usage: python scripts/prepare_inputs.py [--check]
"""

from __future__ import annotations

import argparse
import subprocess
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.windows import Window, from_bounds

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/data"
CLEAN = DATA / "Species_Data/Clean_Data"
BASELINE_BIO1 = DATA / "Bioclim_worldclim_average_1970_2000/wc2.1_10m_bio/Clipped/In_tiff_format/Bio1.tif"
ELEV_DIR = DATA / "Elevation"
ELEV_URL = "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_elev.zip"


def occurrences() -> None:
    sm = gpd.read_file(CLEAN / "spongy_moth_(formerly_gypsy_moth)_(Lymantria_dispar).gpkg")
    sm_keep = sm[sm["state"] != "washington"]
    sm_keep.to_file(CLEAN / "spongy_moth_est_noWA.gpkg", driver="GPKG")
    rw = gpd.read_file(CLEAN / "Root_Weevil_Diaprepes_abbreviatus_2012_2023.gpkg")
    # EPPO Global Database (accessed 13 Oct 2026): present in FL, TX, CA, LA;
    # Mississippi "absent, unreliable record"; AL, GA, SC not listed.
    rw_keep = rw[rw["state"].isin(["florida", "texas", "california", "louisiana"])]
    rw_keep.to_file(CLEAN / "Root_Weevil_est_EPPO.gpkg", driver="GPKG")
    print(f"spongy moth: {len(sm)} -> {len(sm_keep)} records (Washington removed)")
    print(f"root weevil: {len(rw)} -> {len(rw_keep)} records (FL, TX, CA, LA kept)")


def elevation() -> Path:
    src_dir = ELEV_DIR / "worldclim"
    src_dir.mkdir(parents=True, exist_ok=True)
    tif = src_dir / "wc2.1_10m_elev.tif"
    if not tif.exists():
        z = src_dir / "wc2.1_10m_elev.zip"
        if not z.exists():
            subprocess.run(["curl", "-sS", "-L", "-m", "600", "-o", str(z), ELEV_URL], check=True)
        with zipfile.ZipFile(z) as zz:
            zz.extractall(src_dir)
    out = ELEV_DIR / "wc2.1_10m_elev_clipped.tif"
    with rasterio.open(BASELINE_BIO1) as t, rasterio.open(tif) as src:
        keep = ~t.read(1, masked=True).mask
        win = from_bounds(*t.bounds, transform=src.transform)
        win = Window(round(win.col_off), round(win.row_off), round(win.width), round(win.height))
        arr = src.read(1, window=win).astype("float32")
        if src.nodata is not None:
            arr[arr == src.nodata] = np.nan
        assert arr.shape == keep.shape, (arr.shape, keep.shape)
        arr[~keep] = np.nan
        prof = t.profile.copy()
        prof.update(dtype="float32", nodata=np.nan, compress="deflate", count=1, transform=src.window_transform(win))
        with rasterio.open(out, "w", **prof) as d:
            d.write(arr, 1)
    print(f"elevation: {out.name}, {int(np.isfinite(arr).sum())} valid cells (baseline land mask: {int(keep.sum())}), "
          f"range {np.nanmin(arr):.0f} to {np.nanmax(arr):.0f} m; cells baseline-valid but elevation missing: {int((keep & ~np.isfinite(arr)).sum())}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only report what the files contain")
    args = ap.parse_args()
    if not args.check:
        occurrences()
        elevation()
    for f in ["spongy_moth_est_noWA.gpkg", "Root_Weevil_est_EPPO.gpkg"]:
        g = gpd.read_file(CLEAN / f)
        print(f"{f}: {len(g)} records, states {sorted(g['state'].unique())}")
    with rasterio.open(ELEV_DIR / "wc2.1_10m_elev_clipped.tif") as e:
        print("elevation valid cells:", int(np.isfinite(e.read(1)).sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
