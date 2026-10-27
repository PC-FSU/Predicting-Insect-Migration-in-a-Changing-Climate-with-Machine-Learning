#!/usr/bin/env python3
"""Coverage, thresholds, latitudinal shift and GCM spread from projected suitability rasters.

Reads every run (experiment_states.pkl + GeoTIFFs) of one m/feature/beta under
--results. For each run it derives presence-based thresholds from the fitted
model and computes, for the baseline and for each SSP x period (and, when
--gcm-root is given, each GCM):

  * area-weighted mean cloglog suitability (continuous output)
  * suitable area (km^2) and share of the land area for thresholds 0.5, P10
    (10th percentile of training-presence predictions) and maxSSS (maximum
    sensitivity + specificity on training presences vs training background)
  * suitability-weighted centroid latitude of the continuous output
  * centroid, 5th-percentile (trailing edge) and 95th-percentile (leading edge)
    latitudes of the P10 binary map (area-weighted)
  * overlap: share of the baseline P10 area that stays suitable (retained) and
    share of the future P10 area that was not suitable in the baseline (new)
  * novelty: share of land (and of the future P10 area) where at least one
    predictor lies outside its training range (elapid clamps these cells)

Changes are paired within a run (future minus baseline). Summaries give mean,
SD and a percentile bootstrap 95 % CI of the mean over runs, plus the share of
runs with a positive change. With a GCM root the climate-model spread (SD of
GCM means) is reported next to the sampling spread (SD over runs within a GCM).

Cell areas use the spherical cell area at each latitude; land cells are the
cells with a valid baseline prediction that are also valid in the future layers.

Usage:
    python scripts/analyze_projections.py --results runs/revision_main --m 0.25 \
        --gcm-root runs/revision_gcm --out docs/tables/projections
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import rasterio

SHORT = {"Brown_Marmorated_Stink_bug": "BMSB", "Corn_Earworm": "CE", "Spongy_Moth": "SM", "Root_Weevil": "RW", "Spotted_Lanternfly": "SL"}
SSPS = ["126", "245", "370", "585"]
PERIODS = {"2040": "2021_2040", "2060": "2041_2060"}
R_EARTH_KM = 6371.0088
ROOT_DATA = Path(__file__).resolve().parents[1] / "data/data"
# Future WorldClim layers (all SSPs, periods and GCMs share this land mask) have 221
# fewer coastal cells than the baseline layers; areas are compared on the common cells.
with rasterio.open(ROOT_DATA / "SSP_245/Bioclim_worldclim_average_2041_2060/Clipped/In_tiff_format/Bio1.tif") as _src:
    FUTURE_MASK = np.isfinite(_src.read(1))


def cell_area_km2(src: rasterio.DatasetReader) -> np.ndarray:
    """Area of every cell (km^2) for a regular lon/lat grid."""
    t = src.transform
    dlon, dlat = abs(t.a), abs(t.e)
    rows = np.arange(src.height)
    lat_top = t.f + rows * t.e
    lat_bot = lat_top + t.e
    band = (R_EARTH_KM ** 2) * np.deg2rad(dlon) * np.abs(np.sin(np.deg2rad(lat_top)) - np.sin(np.deg2rad(lat_bot)))
    return np.repeat(band[:, None], src.width, axis=1)


def cell_lat(src: rasterio.DatasetReader) -> np.ndarray:
    t = src.transform
    lat_c = t.f + (np.arange(src.height) + 0.5) * t.e
    return np.repeat(lat_c[:, None], src.width, axis=1)


def read(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1).astype("float64")
        a[(a == src.nodata) | ~np.isfinite(a)] = np.nan
    return a


def wquantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    if values.size == 0:
        return np.nan
    o = np.argsort(values); v, w = values[o], weights[o]
    c = np.cumsum(w) / w.sum()
    return float(v[np.searchsorted(c, q, side="left").clip(0, len(v) - 1)])


def maxsss_threshold(p_pres: np.ndarray, p_bg: np.ndarray) -> float:
    grid = np.unique(np.concatenate([p_pres, p_bg]))
    if grid.size > 2000:
        grid = np.quantile(grid, np.linspace(0, 1, 2000))
    best, best_t = -1.0, np.nan
    for t in grid:
        sens = (p_pres >= t).mean(); spec = (p_bg < t).mean()
        if sens + spec > best:
            best, best_t = sens + spec, t
    return float(best_t)


def metrics(arr: np.ndarray, land: np.ndarray, area: np.ndarray, lat: np.ndarray, thresholds: dict,
            base_p10_mask: np.ndarray | None = None, novel: np.ndarray | None = None) -> dict:
    v = land & np.isfinite(arr)
    a, w, la = arr[v], area[v], lat[v]
    out = {"mean_suit": float((a * w).sum() / w.sum()), "centroid_lat_cont": float((a * w * la).sum() / (a * w).sum())}
    for name, t in thresholds.items():
        s = a >= t
        out[f"area_{name}"] = float(w[s].sum())
        out[f"share_{name}"] = float(w[s].sum() / w.sum())
        if name == "p10":
            out["centroid_lat_bin"] = float((w[s] * la[s]).sum() / w[s].sum()) if s.any() else np.nan
            out["lat_p05"] = wquantile(la[s], w[s], 0.05)
            out["lat_p95"] = wquantile(la[s], w[s], 0.95)
            if base_p10_mask is not None:
                b = base_p10_mask[v]
                # share of the baseline P10 area that stays suitable, and share of the future area that is new
                out["retained_share"] = float(w[s & b].sum() / w[b].sum()) if b.any() else np.nan
                out["new_share"] = float(w[s & ~b].sum() / w[s].sum()) if s.any() else np.nan
    if novel is not None:
        n = novel[v]
        out["novel_share"] = float(w[n].sum() / w.sum())              # land with a predictor outside the training range
        if base_p10_mask is not None:
            s = a >= thresholds["p10"]
            out["novel_share_in_p10"] = float(w[s & n].sum() / w[s].sum()) if s.any() else np.nan
    return out


def novel_mask(run_dir: Path, cols: list, lo: pd.Series, hi: pd.Series, layer_dir: Path, elev_path: Path, shape: tuple) -> np.ndarray:
    """Cells where any predictor lies outside its training range (elapid clamps them)."""
    novel = np.zeros(shape, dtype=bool)
    for c in cols:
        if c == "elevation":
            continue  # elevation does not change between periods
        f = layer_dir / f"{c}.tif"
        if not f.exists():
            return novel
        with rasterio.open(f) as src:
            x = src.read(1).astype("float64")
        novel |= np.isfinite(x) & ((x < lo[c]) | (x > hi[c]))
    return novel


def boot_ci(x: np.ndarray, n_boot: int, rng: np.random.Generator) -> tuple[float, float]:
    x = x[np.isfinite(x)]
    if x.size < 2:
        return np.nan, np.nan
    idx = rng.integers(0, x.size, size=(n_boot, x.size))
    m = x[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default="runs/revision_main")
    ap.add_argument("--pathway", default="SSP_245")
    ap.add_argument("--m", default="0.25")
    ap.add_argument("--feature", default="lph")
    ap.add_argument("--beta", default="2.0")
    ap.add_argument("--gcm-root", default=None)
    ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--out", default="docs/tables/projections")
    args = ap.parse_args()
    rng = np.random.default_rng(7)

    rows = []
    for species, short in SHORT.items():
        states = sorted(glob.glob(f"{args.results}/{args.pathway}/{species}/{args.m}/{args.feature}/{args.beta}/*/experiment_states.pkl"))
        for sp in states:
            run_dir = Path(sp).parent
            s = joblib.load(sp)
            model = s["model"]
            p_tr_pres = model.predict(s["x_train"][s["y_train"] == 1])
            p_tr_bg = model.predict(s["x_train"][s["y_train"] == 0])
            thresholds = {"05": 0.5, "p10": float(np.percentile(p_tr_pres, 10)), "maxsss": maxsss_threshold(p_tr_pres, p_tr_bg)}
            cols = list(s["x_train"].columns); lo, hi = s["x_train"].min(), s["x_train"].max()
            seed = s.get("seed"); del s
            with rasterio.open(run_dir / "current.tif") as src:
                area, lat = cell_area_km2(src), cell_lat(src)
            cur = read(run_dir / "current.tif")
            # compare periods only over cells valid in the baseline and in the future layers
            land = np.isfinite(cur) & FUTURE_MASK
            base = metrics(cur, land, area, lat, thresholds)
            base_mask = land & (cur >= thresholds["p10"])
            common = dict(species=short, run=run_dir.name, seed=seed, t_p10=thresholds["p10"], t_maxsss=thresholds["maxsss"])
            rows.append(dict(common, gcm="ACCESS-CM2", ssp="baseline", period="1970_2000", **base))
            from maxent_insect_dir import config as _cfg
            for ssp in SSPS:
                for year, period in PERIODS.items():
                    f = run_dir / (f"{year}.tif" if f"SSP_{ssp}" == args.pathway else f"SSP_{ssp}_{year}.tif")
                    if f.exists():
                        nov = novel_mask(run_dir, cols, lo, hi, Path(_cfg.config_worldclim[f"SSP_{ssp}"][period]), Path(_cfg.PATH_TO_ELEVATION_DATA), cur.shape)
                        rows.append(dict(common, gcm="ACCESS-CM2", ssp=ssp, period=period, **metrics(read(f), land, area, lat, thresholds, base_mask, nov)))
                    if args.gcm_root:
                        for g in sorted(glob.glob(f"{args.gcm_root}/{species}/{run_dir.name}/*_ssp{ssp}_{period}.tif")):
                            gcm = Path(g).name.split(f"_ssp{ssp}")[0]
                            if gcm == "ACCESS-CM2":
                                continue  # already covered by the run's own files
                            gdir = ROOT_DATA / "GCM_ensemble" / gcm / f"ssp{ssp}" / period / "Clipped" / "In_tiff_format"
                            nov = novel_mask(run_dir, cols, lo, hi, gdir, Path(_cfg.PATH_TO_ELEVATION_DATA), cur.shape)
                            rows.append(dict(common, gcm=gcm, ssp=ssp, period=period, **metrics(read(g), land, area, lat, thresholds, base_mask, nov)))
        print(species, "runs:", len(states), flush=True)

    df = pd.DataFrame(rows)
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(f"{out}_long.csv", index=False)

    # paired changes: future minus baseline within run
    base = df[df.ssp == "baseline"].set_index(["species", "run"])
    fut = df[df.ssp != "baseline"].copy()
    metric_cols = [c for c in df.columns if c.startswith(("mean_suit", "centroid", "lat_", "area_", "share_"))]
    for c in metric_cols:
        fut[f"d_{c}"] = fut[c].values - base.loc[list(zip(fut.species, fut.run)), c].values
    for name in ("05", "p10", "maxsss"):
        fut[f"pct_area_{name}"] = 100.0 * fut[f"d_area_{name}"] / base.loc[list(zip(fut.species, fut.run)), f"area_{name}"].values
    fut.to_csv(f"{out}_changes.csv", index=False)

    # summaries over runs, per species x gcm x ssp x period
    summ_rows = []
    keys = ["species", "gcm", "ssp", "period"]
    for k, g in fut.groupby(keys):
        rec = dict(zip(keys, k)); rec["n"] = len(g)
        for c in ["pct_area_05", "pct_area_p10", "pct_area_maxsss", "d_share_p10", "d_mean_suit", "d_centroid_lat_cont", "d_centroid_lat_bin", "d_lat_p05", "d_lat_p95", "retained_share", "new_share", "novel_share", "novel_share_in_p10"]:
            if c not in g.columns:
                continue
            x = g[c].values.astype(float)
            lo, hi = boot_ci(x, args.n_boot, rng)
            rec[f"{c}_mean"], rec[f"{c}_sd"], rec[f"{c}_lo"], rec[f"{c}_hi"], rec[f"{c}_pos"] = float(np.nanmean(x)), float(np.nanstd(x, ddof=1)), lo, hi, float(np.nanmean(x > 0))
        summ_rows.append(rec)
    summ = pd.DataFrame(summ_rows)
    summ.to_csv(f"{out}_summary.csv", index=False)

    # baseline summary
    bsum = base.groupby("species").agg(n=("mean_suit", "size"), share_05=("share_05", "mean"), share_05_sd=("share_05", "std"), share_p10=("share_p10", "mean"), share_p10_sd=("share_p10", "std"), share_maxsss=("share_maxsss", "mean"), share_maxsss_sd=("share_maxsss", "std"), area_p10=("area_p10", "mean"), t_p10=("t_p10", "mean"), t_maxsss=("t_maxsss", "mean"), centroid_lat_cont=("centroid_lat_cont", "mean"), centroid_lat_bin=("centroid_lat_bin", "mean"), lat_p05=("lat_p05", "mean"), lat_p95=("lat_p95", "mean"))
    bsum.to_csv(f"{out}_baseline.csv")

    # GCM decomposition: sampling SD (within GCM, over runs) vs climate-model SD (between GCM means)
    if args.gcm_root:
        dec = []
        for (sp, ssp, period), g in fut.groupby(["species", "ssp", "period"]):
            if g.gcm.nunique() < 2:
                continue
            for c in ["pct_area_p10", "d_centroid_lat_cont"]:
                per_gcm = g.groupby("gcm")[c].agg(["mean", "std"])
                dec.append(dict(species=sp, ssp=ssp, period=period, metric=c, n_gcm=len(per_gcm), grand_mean=per_gcm["mean"].mean(), sd_between_gcm=per_gcm["mean"].std(ddof=1), sd_within_gcm=per_gcm["std"].mean(), gcm_means=json.dumps(per_gcm["mean"].round(2).to_dict())))
        pd.DataFrame(dec).to_csv(f"{out}_gcm_decomposition.csv", index=False)

    print("wrote", f"{out}_long.csv", f"{out}_changes.csv", f"{out}_summary.csv", f"{out}_baseline.csv")
    print(bsum.round(4).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
