#!/usr/bin/env python3
"""Replicated background-drift experiment (revision of Section 3.3 / Figure 11).

Design (one species, bioclimatic predictors only, fixed predictor set):

1. Base model: thinned presences, one seeded background draw B0 with mixing
   coefficient m, correlation filter -> predictor set C (kept fixed for every
   refit below), 50 km checkerboard split, MaxEnt fit, permutation importance
   on the test fold (I0).
2. Drift: for each level d in --levels (km) and each of --replicates, every
   background point is moved by a random direction (uniform on the circle) and
   a random distance (uniform in [0, d]) in the equal-area CRS (EPSG:5070).
   Points that land on a no-data climate cell are dropped and counted. The
   model is refitted on the moved background with the same presences, folds
   and predictors; importance I_d,r is compared with I0.
3. Fresh redraws: --replicates new seeded background draws (no drift) are
   fitted the same way, to show how much the ranking moves when the
   background is simply resampled.

Reported per fit: Spearman and Kendall rank correlation of the importance
vector with I0, overlap of the top-3 and top-5 sets, the fraction of
background points whose 10-arc-min raster cell changed, and the number of
points dropped. Predictor values are read as the value of the raster cell
containing the point (elapid.annotate, no interpolation).

Usage:
    python scripts/drift_experiment.py --species Brown_Marmorated_Stink_bug \
        --out runs/revision_drift --replicates 10
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import elapid as ela
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from scipy.stats import kendalltau, spearmanr

from maxent_insect_dir import config, prepare_metadata, run_utils, utils

os.environ.setdefault("MPLBACKEND", "Agg")


def annotate_bioclim(points: gpd.GeoDataFrame, rasters: list[str], labels: list[str]) -> gpd.GeoDataFrame:
    return run_utils.annotate(points[["geometry"]], rasters, labels=labels, drop_na=True)


def cell_ids(points: gpd.GeoDataFrame, raster_path: str) -> np.ndarray:
    ll = points.to_crs(4326)
    with rasterio.open(raster_path) as src:
        rows, cols = rasterio.transform.rowcol(src.transform, ll.geometry.x.values, ll.geometry.y.values)
    return np.asarray(rows) * 100000 + np.asarray(cols)


def fit_and_score(presence_train, presence_test, background, test_bg, cols, tau, beta, feature):
    df_train = ela.stack_geodataframes(presence_train[cols + ["geometry"]], background[cols + ["geometry"]], add_class_label=True)
    df_test = ela.stack_geodataframes(presence_test[cols + ["geometry"]], test_bg[cols + ["geometry"]], add_class_label=True)
    x_train, y_train = df_train.drop(columns=["class", "geometry"]), df_train["class"]
    x_test, y_test = df_test.drop(columns=["class", "geometry"]), df_test["class"]
    model = run_utils.train_model(x_train, y_train, cat_indices=[], tau=tau, beta_multiplier=beta, feature_type=feature)
    imp = utils.get_feature_importance(model, x_test, y_test)
    cbi = run_utils.Continuous_boyce_index.continuous_boyce_index(
        yobs=model.predict(x_test[y_test == 1]), ypred=model.predict(x_test[y_test == 0]), nbins=20
    )["Spearman.cor"]
    return imp.astype(float), float(cbi)


def compare(i0: pd.Series, i1: pd.Series) -> dict:
    a, b = i0.reindex(i1.index).values, i1.values
    r0 = i0.rank(ascending=False); r1 = i1.rank(ascending=False)
    top = lambda r, k: set(r[r <= k].index)  # noqa: E731
    return {
        "spearman": float(spearmanr(a, b).correlation),
        "kendall": float(kendalltau(a, b).correlation),
        "top3_overlap": len(top(r0, 3) & top(r1, 3)),
        "top5_overlap": len(top(r0, 5) & top(r1, 5)),
        "top1_same": int(r0.idxmin() == r1.idxmin()),
        "mean_abs_change": float(np.mean(np.abs(a - b))),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--species", default="Brown_Marmorated_Stink_bug")
    ap.add_argument("--m", type=float, default=0.25)
    ap.add_argument("--beta", type=float, default=2.0)
    ap.add_argument("--feature", default="lph")
    ap.add_argument("--levels", type=float, nargs="+", default=[1, 5, 10, 50], help="drift levels in km")
    ap.add_argument("--replicates", type=int, default=10)
    ap.add_argument("--seed", type=int, default=5000)
    ap.add_argument("--thin-distance", type=float, default=10000)
    ap.add_argument("--background-count", type=int, default=10000)
    ap.add_argument("--out", default="runs/revision_drift")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    data, labels = prepare_metadata.prepare_experiment_metadata(config.config_worldclim["SSP_245"], "1970_2000")
    rasters, bio_labels = data["train"]["bioclim"]["rasters"], labels["bioclim"]
    tau = config.tau[args.species]

    # --- base draw --------------------------------------------------------
    np.random.seed(args.seed)
    presence, b0 = run_utils.get_presence_background(
        args.species, rasters[0], to_thin=True, bias_uniform_mix_coeff=args.m,
        background_count=args.background_count, thinning_distance=args.thin_distance,
    )
    presence = annotate_bioclim(presence, rasters, bio_labels)
    b0_raw = b0.copy()
    b0 = annotate_bioclim(b0_raw, rasters, bio_labels)
    merged = ela.stack_geodataframes(presence, b0, add_class_label=False)
    cols = list(utils.remove_highly_correlated(merged[bio_labels], threshold=0.9).columns)
    print(f"predictors kept ({len(cols)}): {cols}")
    pres_train, pres_test = utils.get_train_test_split(presence)
    test_bg = annotate_bioclim(gpd.read_file(config.PATH_TO_TEST_DATA)[["geometry"]], rasters, bio_labels)
    i0, cbi0 = fit_and_score(pres_train, pres_test, b0, test_bg, cols, tau, args.beta, args.feature)
    base_cells = cell_ids(b0_raw, rasters[0])
    print(f"base CBI {cbi0:.3f}; top-5: {list(i0.sort_values(ascending=False).index[:5])}; {time.time()-t0:.0f}s")

    records, importances = [], [dict(condition="base", level_km=0.0, replicate=0, cbi=cbi0, **i0.to_dict())]

    # --- drifted backgrounds ---------------------------------------------
    rng = np.random.default_rng(args.seed + 1)
    for d in args.levels:
        for r in range(args.replicates):
            theta = rng.uniform(0, 2 * np.pi, len(b0_raw))
            dist = rng.uniform(0, d * 1000.0, len(b0_raw))
            moved = b0_raw.copy()
            moved["geometry"] = gpd.points_from_xy(
                b0_raw.geometry.x + dist * np.cos(theta), b0_raw.geometry.y + dist * np.sin(theta), crs=b0_raw.crs
            )
            moved_cells = cell_ids(moved, rasters[0])
            frac_changed = float((moved_cells != base_cells).mean())
            moved_ann = annotate_bioclim(moved, rasters, bio_labels)
            n_dropped = len(moved) - len(moved_ann)
            imp, cbi = fit_and_score(pres_train, pres_test, moved_ann, test_bg, cols, tau, args.beta, args.feature)
            rec = dict(condition="drift", level_km=d, replicate=r, cbi=cbi, frac_cell_changed=frac_changed, n_dropped=n_dropped, **compare(i0, imp))
            records.append(rec); importances.append(dict(condition="drift", level_km=d, replicate=r, cbi=cbi, **imp.to_dict()))
            print(f"drift {d:>4.0f} km rep {r}: cells changed {frac_changed:.3f}, dropped {n_dropped}, rho {rec['spearman']:.3f}, top3 {rec['top3_overlap']}, CBI {cbi:.3f}; {time.time()-t0:.0f}s", flush=True)
            pd.DataFrame(records).to_csv(out / "drift_summary.csv", index=False)
            pd.DataFrame(importances).to_csv(out / "drift_importances.csv", index=False)

    # --- fresh redraws (no drift) ------------------------------------------
    for r in range(args.replicates):
        np.random.seed(args.seed + 100 + r)
        _, bg = run_utils.get_presence_background(
            args.species, rasters[0], to_thin=True, bias_uniform_mix_coeff=args.m,
            background_count=args.background_count, thinning_distance=args.thin_distance,
        )
        bg = annotate_bioclim(bg, rasters, bio_labels)
        imp, cbi = fit_and_score(pres_train, pres_test, bg, test_bg, cols, tau, args.beta, args.feature)
        rec = dict(condition="redraw", level_km=np.nan, replicate=r, cbi=cbi, frac_cell_changed=np.nan, n_dropped=np.nan, **compare(i0, imp))
        records.append(rec); importances.append(dict(condition="redraw", level_km=np.nan, replicate=r, cbi=cbi, **imp.to_dict()))
        print(f"redraw rep {r}: rho {rec['spearman']:.3f}, top3 {rec['top3_overlap']}, CBI {cbi:.3f}; {time.time()-t0:.0f}s", flush=True)
        pd.DataFrame(records).to_csv(out / "drift_summary.csv", index=False)
        pd.DataFrame(importances).to_csv(out / "drift_importances.csv", index=False)

    meta = dict(vars(args), predictors=cols, n_presence=int(len(presence)), n_train_presence=int(len(pres_train)),
                n_test_presence=int(len(pres_test)), n_background=int(len(b0)), tau=tau, base_cbi=cbi0, elapsed_s=time.time() - t0)
    (out / "meta.json").write_text(json.dumps(meta, indent=2, default=str))
    print("done", json.dumps({k: meta[k] for k in ('n_presence', 'n_background', 'base_cbi', 'elapsed_s')}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
