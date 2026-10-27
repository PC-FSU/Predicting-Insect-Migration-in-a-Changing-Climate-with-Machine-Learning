#!/usr/bin/env python3
"""Simple quality checks of the occurrence records used (Section 2.2.1).

For the record files used by the models (spongy moth without Washington,
root weevil from the EPPO-present states, the other three complete) it reports:
records without a year, records dated 2000 or earlier (inside the 1970-2000
climate baseline), records within 1 km of a state centroid (GADM level-1
layer data/data/US_shapefile), and coordinates with one or no decimals
(precision of about 10 km or worse), with the number of distinct sites.
Writes docs/tables/record_checks.txt.

Usage: python scripts/record_checks.py
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data/data/Species_Data/Clean_Data"
FILES = {"BMSB": "Brown_Marmorated_Stink_Bug_Halyomorpha_halys_1999_2023.gpkg", "CE": "Corn_Earworm_Helicoverpa_Zea_2004_2023.gpkg",
         "SM": "spongy_moth_est_noWA.gpkg", "RW": "Root_Weevil_est_EPPO.gpkg", "SL": "spotted_lanternfly_(Lycorma_delicatula).gpkg"}


def decimals(v: np.ndarray) -> np.ndarray:
    out = []
    for x in np.abs(v):
        t = ("%.8f" % x).rstrip("0")
        out.append(len(t.split(".")[1]) if "." in t else 0)
    return np.array(out)


def main() -> int:
    states = gpd.read_file(ROOT / "data/data/US_shapefile/US_shapefile.shp").to_crs(5070)
    tree = cKDTree(np.c_[states.geometry.centroid.x, states.geometry.centroid.y])
    lines = []
    for code, f in FILES.items():
        g = gpd.read_file(CLEAN / f)
        year = pd.to_numeric(g["year"], errors="coerce")
        p = g.to_crs(5070); dist, _ = tree.query(np.c_[p.geometry.x, p.geometry.y])
        w = g.to_crs(4326); dec = np.minimum(decimals(w.geometry.x.values), decimals(w.geometry.y.values))
        low = w[dec <= 1]
        sites = len(set(zip(low.geometry.x.round(4), low.geometry.y.round(4))))
        lines.append(f"{code}: {len(g)} records; without year {int(year.isna().sum())}; year {int(year.min())}-{int(year.max())}; "
                     f"dated <= 2000: {int((year <= 2000).sum())}; within 1 km of a state centroid: {int((dist < 1000).sum())}; "
                     f"coordinates with <= 1 decimal: {len(low)} records at {sites} distinct sites")
    text = "\n".join(lines)
    print(text)
    (ROOT / "docs/tables/record_checks.txt").write_text(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
