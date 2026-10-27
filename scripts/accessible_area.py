#!/usr/bin/env python3
"""Accessible areas (M) for each species on the 10 arc-min climate grid.

The background-sampling analysis is repeated inside an ecologically
meaningful accessible area M per species (occupied ecoregions, a dispersal
buffer), under alternative definitions.
All masks are built on the grid of the baseline climate layers (348 x 150
cells) and limited to cells with baseline climate data:

  eco      EPA Level III ecoregions that contain at least one thinned record
  eco100   the same ecoregions plus every cell within 100 km of them
  recNNN   every cell whose centre lies within NNN km of a thinned record

Thinned records are the records used by the models (data_release/
occurrences_<species>.csv, 10 km thinning, records with climate data).
Ecoregions: US EPA Level III ecoregions of the conterminous United States
(data/data/Ecoregions/epa_l3_download/us_eco_l3.shp). A cell takes the
ecoregion of its centre; land cells whose centre falls in no polygon (coast)
take the ecoregion of the nearest coded cell.

Writes data/data/accessible_area/<Species>_<def>.tif (uint8, 1 = inside M)
and docs/tables/accessible_area_summary.csv.

Usage: python -I scripts/accessible_area.py [--defs eco eco100 rec300] [--check-only]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio import features
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
BIO1 = ROOT / "data/data/Bioclim_worldclim_average_1970_2000/wc2.1_10m_bio/Clipped/In_tiff_format/Bio1.tif"
ECO = ROOT / "data/data/Ecoregions/epa_l3_download/us_eco_l3.shp"
OUT = ROOT / "data/data/accessible_area"
SPECIES = {"BMSB": "Brown_Marmorated_Stink_bug", "CE": "Corn_Earworm", "SM": "Spongy_Moth",
           "RW": "Root_Weevil", "SL": "Spotted_Lanternfly"}


def grid():
    with rasterio.open(BIO1) as src:
        valid = ~src.read(1, masked=True).mask
        prof, tr, shape = src.profile.copy(), src.transform, (src.height, src.width)
    rows, cols = np.indices(shape)
    lon, lat = rasterio.transform.xy(tr, rows.ravel(), cols.ravel(), offset="center")
    x, y = Transformer.from_crs(4326, 5070, always_xy=True).transform(np.asarray(lon), np.asarray(lat))
    return valid, prof, tr, shape, np.asarray(x).reshape(shape), np.asarray(y).reshape(shape)


def ecoregion_codes(tr, shape, valid, X, Y):
    eco = gpd.read_file(ECO)[["US_L3CODE", "geometry"]]
    eco["geometry"] = eco.geometry.simplify(500)          # metres in the Albers CRS; cheap and safe at 18 km cells
    eco = eco.to_crs(4326)
    codes = features.rasterize(((g, int(c)) for g, c in zip(eco.geometry, eco.US_L3CODE)), out_shape=shape,
                               transform=tr, fill=0, dtype="int32")
    miss = valid & (codes == 0)
    if miss.any():
        have = valid & (codes > 0)
        t = cKDTree(np.c_[X[have], Y[have]])
        _, i = t.query(np.c_[X[miss], Y[miss]])
        codes[miss] = codes[have][i]
    codes[~valid] = 0
    return codes


def within(X, Y, valid, pts_xy, km):
    d, _ = cKDTree(pts_xy).query(np.c_[X.ravel(), Y.ravel()], distance_upper_bound=km * 1000.0)
    return valid & np.isfinite(d).reshape(X.shape)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--defs", nargs="+", default=["eco", "eco100", "rec300"])
    ap.add_argument("--check-only", action="store_true", help="print the share of land for many candidate definitions, write nothing")
    args = ap.parse_args()
    valid, prof, tr, shape, X, Y = grid()
    codes = ecoregion_codes(tr, shape, valid, X, Y)
    land = int(valid.sum())
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    defs = ["eco", "eco100", "rec100", "rec200", "rec300", "rec500"] if args.check_only else args.defs
    for code, name in SPECIES.items():
        d = pd.read_csv(ROOT / f"data_release/occurrences_{name}.csv")
        pts = np.c_[d.x_epsg5070.values, d.y_epsg5070.values]
        r, c = rasterio.transform.rowcol(tr, d.lon.values, d.lat.values)
        occ = sorted({int(v) for v in codes[np.asarray(r), np.asarray(c)] if v > 0})
        m_eco = valid & np.isin(codes, occ)
        for dn in defs:
            if dn == "eco":
                m = m_eco
            elif dn.startswith("eco"):
                m = within(X, Y, valid, np.c_[X[m_eco], Y[m_eco]], float(dn[3:])) | m_eco
            else:
                m = within(X, Y, valid, pts, float(dn[3:]))
            inside = m[np.asarray(r), np.asarray(c)]
            rows.append(dict(species=code, definition=dn, cells=int(m.sum()), share_of_land=round(m.sum() / land, 3),
                             occupied_ecoregions=len(occ), records=len(d), records_inside=int(inside.sum())))
            if not args.check_only:
                p = prof.copy(); p.update(dtype="uint8", nodata=None, count=1, compress="deflate")
                with rasterio.open(OUT / f"{name}_{dn}.tif", "w", **p) as dst:
                    dst.write(m.astype("uint8"), 1)
    out = pd.DataFrame(rows)
    print(out.pivot(index="species", columns="definition", values="share_of_land").reindex(list(SPECIES)).to_string())
    print(out[["species", "occupied_ecoregions", "records"]].drop_duplicates().to_string(index=False))
    if (out.records_inside < out.records).any():
        print("records outside M:\n", out[out.records_inside < out.records].to_string(index=False))
    if not args.check_only:
        out.to_csv(ROOT / "docs/tables/accessible_area_summary.csv", index=False)
        print("wrote", OUT, "and docs/tables/accessible_area_summary.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
