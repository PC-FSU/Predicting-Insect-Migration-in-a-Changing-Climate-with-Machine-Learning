#!/usr/bin/env python3
"""Export the processed occurrence tables and the fixed test background.

For every species, the thinned presence records that enter the models (after
10 km thinning and removal of records on cells without climate data), with
their checkerboard fold, longitude/latitude (WGS84) and EPSG:5070 coordinates,
are written to data_release/occurrences_<species>.csv. The fixed uniform test
background (20,000 points, 19,898 with climate data) goes to
data_release/test_background.csv. These are the inputs the paper's
Data Availability Statement refers to.

Usage: python scripts/export_processed_data.py [--results runs/revision_main]
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import geopandas as gpd
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_release"
SP = {"Brown_Marmorated_Stink_bug": "Halyomorpha halys", "Corn_Earworm": "Helicoverpa zea", "Spongy_Moth": "Lymantria dispar",
      "Root_Weevil": "Diaprepes abbreviatus", "Spotted_Lanternfly": "Lycorma delicatula"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=str(ROOT / "runs/revision_main"))
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    rows = []
    for species, sci in SP.items():
        states = sorted(glob.glob(f"{args.results}/SSP_245/{species}/0.25/lph/2.0/*/experiment_states.pkl"))
        if not states:
            print("no state for", species); continue
        s = joblib.load(states[0])
        pres = s["presence"][["geometry"]].copy()
        # fold membership: training presences are the first y_train==1 rows of x_train (stacked before background)
        import elapid as ela  # noqa: F401  (import keeps the pickled model loadable)
        from maxent_insect_dir import utils
        train, test = utils.get_train_test_split(pres)
        train_keys = set(zip(train.geometry.x.round(3), train.geometry.y.round(3)))
        test_keys = set(zip(test.geometry.x.round(3), test.geometry.y.round(3)))
        # a record exactly on a grid line is "within" neither cell and is used by no model
        pres["fold"] = ["A_train" if (round(g.x, 3), round(g.y, 3)) in train_keys else ("B_test" if (round(g.x, 3), round(g.y, 3)) in test_keys else "none_on_grid_line") for g in pres.geometry]
        ll = pres.to_crs(4326)
        df = pd.DataFrame({"species": sci, "lon": ll.geometry.x.round(5), "lat": ll.geometry.y.round(5),
                           "x_epsg5070": pres.geometry.x.round(1), "y_epsg5070": pres.geometry.y.round(1), "fold": pres["fold"]})
        df.to_csv(OUT / f"occurrences_{species}.csv", index=False)
        rows.append(dict(species=sci, n=len(df), train=int((df.fold == "A_train").sum()), test=int((df.fold == "B_test").sum()), unused=int((df.fold == "none_on_grid_line").sum())))
        del s
    tb = gpd.read_file(ROOT / "data/data/Test_data/test.gpkg")[["geometry"]]
    ll = tb.to_crs(4326)
    pd.DataFrame({"lon": ll.geometry.x.round(5), "lat": ll.geometry.y.round(5), "x_epsg5070": tb.geometry.x.round(1), "y_epsg5070": tb.geometry.y.round(1)}).to_csv(OUT / "test_background.csv", index=False)
    (OUT / "README.md").write_text(
        "# Processed data release\n\n"
        "Occurrence records after cleaning (positive detections with coordinates inside the contiguous US),\n"
        "10 km greedy thinning in EPSG:5070 and removal of records on cells without climate data, with the\n"
        "checkerboard fold (50 km cells; A_train = training colour, B_test = test colour) used by every model fit.\n"
        "Records outside the established range were removed before thinning: the 71 Washington State spongy moth\n"
        "detections (eradicated introductions) and the 23 root weevil records from Alabama, Georgia, Mississippi and\n"
        "South Carolina, where the EPPO Global Database does not list the species as present.\n"
        "`test_background.csv` is the fixed set of 20,000 uniformly sampled background points used to evaluate\n"
        "every model (points on cells without climate data are dropped when the predictors are read).\n\n"
        "Raw records: EDDMapS (stink bug, corn earworm, spongy moth, spotted lanternfly) and GBIF (Diaprepes root weevil);\n"
        "see the manuscript, Section 2.2.1. Climate: WorldClim 2.1 (baseline 1970-2000) and CMIP6 ACCESS-CM2,\n"
        "MPI-ESM1-2-HR, MIROC6, UKESM1-0-LL, EC-Earth3-Veg (2021-2040, 2041-2060, SSP1-2.6/2-4.5/3-7.0/5-8.5), 10 arc-min.\n\n"
        + "| species | records | train (A) | test (B) | on a grid line (unused) |\n|---|---|---|---|---|\n"
        + "".join(f"| {r['species']} | {r['n']} | {r['train']} | {r['test']} | {r['unused']} |\n" for r in rows))
    print(pd.DataFrame(rows).to_string(index=False)); print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
