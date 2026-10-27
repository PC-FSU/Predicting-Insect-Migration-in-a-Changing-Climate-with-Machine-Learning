#!/usr/bin/env python3
"""Results of the accessible-area runs (Revision 2).

For every species and accessible-area definition M (runs/revision2_M_<def>)
and for the contiguous-US reference (runs/revision_main):
  * test CBI and AUC by m (mean +- SD over 20 seeded repeats; the test
    background is the fixed test set limited to M),
  * the m with the highest mean CBI and the paired difference between m = 0.25
    and that m with a bootstrap 95 % CI (same seeds, so repeats are paired),
  * the relative change of the P10 suitable area under SSP2-4.5 for 2041-2060
    (ACCESS-CM2) at m = 0.25, inside M and over the whole contiguous US, and
    the change of the contiguous-US models (main set) measured inside the same M,
    which separates the effect of the calibration area from that of the area
    over which the change is measured.
Writes docs/tables/accessible_area_results.csv, the table bodies
tables/si_accessible_summary.tex and tables/si_accessible_cbi.tex in the active paper
folder, and figs/accessible_areas.pdf (maps of M).

Usage: python scripts/accessible_area_tables.py [--defs eco eco100 rec200]
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_projections import cell_area_km2, read  # noqa: E402
from table2_stats import boot_ci  # noqa: E402

PAPER = Path(os.environ.get("MAXENT_PAPER_DIR", str(ROOT / "Maxent_Paper/Maxent_Paper_MDPI_Insects_Revision2")))
SP = {"Brown_Marmorated_Stink_bug": "BMSB", "Corn_Earworm": "CE", "Spongy_Moth": "SM", "Root_Weevil": "RW", "Spotted_Lanternfly": "SL"}
MS = [0.0, 0.25, 0.5, 0.75, 1.0]
DEF_NAME = {"us": "Contiguous US", "eco": "Ecoregions", "eco100": "Ecoregions + 100 km", "rec200": "Records + 200 km"}
MASKS = ROOT / "data/data/accessible_area"


def load_states(root: Path, folder: str):
    rows = []
    for m in MS:
        for f in sorted(glob.glob(f"{root}/SSP_245/{folder}/{m}/lph/2.0/*/experiment_states.pkl")):
            s = joblib.load(f)
            p10 = float(np.percentile(s["model"].predict(s["x_train"][s["y_train"] == 1]), 10))
            rows.append(dict(m=m, seed=s.get("seed"), cbi=float(s["cbi_test"]["Spearman.cor"]), auc=float(s["auc"]["AUC_test"]),
                             n_bg=len(s["background"]), n_test_bg=int((s["y_test"] == 0).sum()), p10=p10, run_dir=str(Path(f).parent)))
            del s
    return pd.DataFrame(rows)


def area_change(run_dir: str, t: float, mask: np.ndarray | None) -> float:
    d = Path(run_dir)
    if not (d / "current.tif").exists() or not (d / "2060.tif").exists():
        return np.nan
    with rasterio.open(d / "current.tif") as src:
        area = cell_area_km2(src)
    cur, fut = read(d / "current.tif"), read(d / "2060.tif")
    land = np.isfinite(cur) & np.isfinite(fut)
    if mask is not None:
        land &= mask
    a0, a1 = area[land & (cur >= t)].sum(), area[land & (fut >= t)].sum()
    return 100.0 * (a1 - a0) / a0 if a0 > 0 else np.nan


def summarize(df: pd.DataFrame, mask: np.ndarray | None, rng) -> dict:
    g = df.groupby("m").agg(cbi=("cbi", "mean"), cbi_sd=("cbi", "std"), auc=("auc", "mean"), auc_sd=("auc", "std"), n=("cbi", "size"))
    best = float(g.cbi.idxmax())
    ref = df[df.m == 0.25].sort_values("seed"); bst = df[df.m == best].sort_values("seed")
    if best != 0.25 and len(ref) == len(bst) and (ref.seed.values == bst.seed.values).all():
        diff = ref.cbi.values - bst.cbi.values; lo, hi = boot_ci(diff, 10000, rng); dmean = float(diff.mean())
    else:
        dmean, lo, hi = 0.0, np.nan, np.nan
    r25 = df[df.m == 0.25]
    ch_m = [area_change(r.run_dir, r.p10, mask) for r in r25.itertuples()]
    ch_us = [area_change(r.run_dir, r.p10, None) for r in r25.itertuples()]
    out = dict(best_m=best, cbi_best=g.cbi[best], cbi_best_sd=g.cbi_sd[best], cbi_025=g.cbi.get(0.25, np.nan), cbi_025_sd=g.cbi_sd.get(0.25, np.nan),
               d_025_best=dmean, d_lo=lo, d_hi=hi, auc_min_lt1=g.auc[g.index < 1].min(), auc_max_lt1=g.auc[g.index < 1].max(),
               cbi_m1=g.cbi.get(1.0, np.nan), n_fits=int(g.n.sum()), n_test_bg=int(df.n_test_bg.median()), bg_min=int(df.n_bg.min()),
               d_area_M=np.nanmean(ch_m) if ch_m else np.nan, d_area_M_sd=np.nanstd(ch_m, ddof=1) if len(ch_m) > 1 else np.nan,
               d_area_US=np.nanmean(ch_us) if ch_us else np.nan, d_area_US_sd=np.nanstd(ch_us, ddof=1) if len(ch_us) > 1 else np.nan)
    for m in MS:
        out[f"cbi_{m}"] = g.cbi.get(m, np.nan); out[f"cbi_sd_{m}"] = g.cbi_sd.get(m, np.nan)
        out[f"auc_{m}"] = g.auc.get(m, np.nan); out[f"n_{m}"] = int(g.n.get(m, 0))
    return out


def maps(defs):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    fig, axes = plt.subplots(len(SP), len(defs), figsize=(2.6 * len(defs), 1.45 * len(SP)), dpi=200)
    cmap = ListedColormap(["#e8e6e1", "#3987e5"])
    for i, (folder, code) in enumerate(SP.items()):
        d = pd.read_csv(ROOT / f"data_release/occurrences_{folder}.csv")
        for j, dn in enumerate(defs):
            ax = axes[i, j]
            with rasterio.open(MASKS / f"{folder}_{dn}.tif") as src:
                m = src.read(1).astype(float); b = src.bounds
                with rasterio.open(ROOT / "data/data/Bioclim_worldclim_average_1970_2000/wc2.1_10m_bio/Clipped/In_tiff_format/Bio1.tif") as bio:
                    valid = ~bio.read(1, masked=True).mask
            m[~valid] = np.nan
            ax.imshow(m, extent=(b.left, b.right, b.bottom, b.top), cmap=cmap, vmin=0, vmax=1, interpolation="nearest")
            ax.scatter(d.lon, d.lat, s=0.15, color="#0b0b0b", linewidths=0)
            ax.set_xticks([]); ax.set_yticks([])
            for sp_ in ax.spines.values():
                sp_.set_visible(False)
            if i == 0:
                ax.set_title(DEF_NAME[dn], fontsize=7)
            if j == 0:
                ax.set_ylabel(code, fontsize=7)
    fig.tight_layout(pad=0.3)
    out = PAPER / "figs/accessible_areas.pdf"
    fig.savefig(out, bbox_inches="tight"); plt.close(fig); print("wrote", out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--defs", nargs="+", default=["eco", "eco100", "rec200"])
    ap.add_argument("--no-maps", action="store_true")
    args = ap.parse_args()
    rng = np.random.default_rng(2026)
    share = pd.read_csv(ROOT / "docs/tables/accessible_area_summary.csv")
    rows, us_ref = [], {}
    for folder, code in SP.items():
        for dn in ["us"] + args.defs:
            root = ROOT / ("runs/revision_main" if dn == "us" else f"runs/revision2_M_{dn}")
            df = load_states(root, folder)
            if df.empty:
                continue
            mask = None
            if dn != "us":
                with rasterio.open(MASKS / f"{folder}_{dn}.tif") as src:
                    mask = src.read(1) == 1
            r = summarize(df, mask, rng)
            if dn == "us" and r["best_m"] != 0.25:  # same CI as Table 3 of the main text
                t2 = pd.read_csv(ROOT / "docs/tables/table2_revision_stats.csv")
                row = t2[(t2.species == code) & (t2.m == r["best_m"])].iloc[0]
                r["d_025_best"], r["d_lo"], r["d_hi"] = row.delta_cbi, row.ci_lo, row.ci_hi
            if dn != "us":  # the contiguous-US models of the main set, measured inside the same M
                ref = us_ref[folder]
                r["d_area_M_usmodel"] = float(np.nanmean([area_change(d_, t_, mask) for d_, t_ in ref]))
            else:
                us_ref[folder] = [(row.run_dir, row.p10) for row in df[df.m == 0.25].itertuples()]
                r["d_area_M_usmodel"] = np.nan
            sh = 1.0 if dn == "us" else float(share[(share.species == code) & (share.definition == dn)].share_of_land.iloc[0])
            rows.append(dict(species=code, definition=dn, share_of_land=sh, **r))
            print(f"{code} {dn:7s} n={r['n_fits']:3d} best m={r['best_m']:.2f} CBI best {r['cbi_best']:.3f} | m=0.25 {r['cbi_025']:.3f} "
                  f"(d {r['d_025_best']:+.3f} [{r['d_lo']:+.3f},{r['d_hi']:+.3f}]) | CBI m=1 {r['cbi_m1']:.3f} | AUC m<1 {r['auc_min_lt1']:.3f}-{r['auc_max_lt1']:.3f} "
                  f"| dArea M {r['d_area_M']:+.0f} US {r['d_area_US']:+.0f} US-model in M {r['d_area_M_usmodel']:+.0f} | test bg {r['n_test_bg']}")
    res = pd.DataFrame(rows)
    res.to_csv(ROOT / "docs/tables/accessible_area_results.csv", index=False)
    # main-text table: one row per species and definition
    def num(v, d=3, sign=False):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "--"
        t = f"{v:+.{d}f}" if sign else f"{v:.{d}f}"
        if float(t) == 0:  # no negative zero
            t = t.lstrip("+-")
        return t.replace("-", "$-$")
    body, si = [], []
    for code in SP.values():
        x = res[res.species == code].to_dict("records")
        for k, r in enumerate(x):
            d = "--" if r["best_m"] == 0.25 else f"{num(r['d_025_best'], sign=True)} [{num(r['d_lo'], sign=True)}, {num(r['d_hi'], sign=True)}]"
            area_m = num(r["d_area_US"] if r["definition"] == "us" else r["d_area_M"], 0, sign=True)
            body.append(f"{code if k == 0 else ''} & {DEF_NAME[r['definition']]} & {100*r['share_of_land']:.0f} & {r['best_m']:.2f} & "
                        f"{num(r['cbi_best'])} & {num(r['cbi_025'])} & {d} & {num(r['auc_min_lt1'])}--{num(r['auc_max_lt1'])} & "
                        f"{area_m} & {'--' if r['definition'] == 'us' else num(r['d_area_M_usmodel'], 0, sign=True)} \\\\")
            si.append(f"{code if k == 0 else ''} & {DEF_NAME[r['definition']]} & "
                      + " & ".join(f"{num(r[f'cbi_{m}'])} $\\pm$ {num(r[f'cbi_sd_{m}'])}" for m in MS) + " \\\\")
        body.append("\\midrule"); si.append("\\midrule")
    (PAPER / "tables").mkdir(parents=True, exist_ok=True)
    (PAPER / "tables/si_accessible_summary.tex").write_text("\n".join(body[:-1]) + "\n")
    (PAPER / "tables/si_accessible_cbi.tex").write_text("\n".join(si[:-1]) + "\n")
    print("wrote tables/si_accessible_summary.tex, tables/si_accessible_cbi.tex, docs/tables/accessible_area_results.csv")
    if not args.no_maps:
        maps(args.defs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
