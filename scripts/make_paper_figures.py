#!/usr/bin/env python3
"""Figures of the revised manuscript from the run outputs.

  maps      Figures 4-5 (baseline suitability by m, CE and SM) and Figures 6-10
            (baseline / 2021-2040 / 2041-2060 under SSP2-4.5 per species), mean
            of the 20 fits of the reference setting.
  drift     Figure 11: Spearman correlation with the base fit by condition, and
            the scores of the six leading predictors by displacement level.
  change    Figure 12: relative change of the P10 area and centroid shift for
            2041-2060 by pathway (ACCESS-CM2 mean with 95 % CI; other GCMs as
            small markers).

Style: one blue sequential ramp (light = low suitability) for maps, fixed
categorical slots for pathways / conditions, thin marks, hairline axes.

Usage: python scripts/make_paper_figures.py [maps|drift|change|all] [--results runs/revision_main]
"""

from __future__ import annotations

import argparse
import os
import glob
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import LinearSegmentedColormap

matplotlib.use("Agg")
ROOT = Path(__file__).resolve().parents[1]
FIGS = Path(os.environ.get("MAXENT_PAPER_DIR", str(ROOT / "Maxent_Paper/Maxent_Paper_MDPI_Insects_Revision2"))) / "figs"  # active version (Revision 2)
SP = {"Brown_Marmorated_Stink_bug": "BMSB", "Corn_Earworm": "CE", "Spongy_Moth": "SM", "Root_Weevil": "RW", "Spotted_Lanternfly": "SL"}
NAMES = {"BMSB": "Brown marmorated stink bug", "CE": "Corn earworm", "SM": "Spongy moth", "RW": "Diaprepes root weevil", "SL": "Spotted lanternfly"}
# reference palette (dataviz skill): sequential blue ramp and categorical slots
SEQ = ["#fcfcfb", "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
GRAY, INK, INK2 = "#9a9893", "#0b0b0b", "#52514e"
CMAP = LinearSegmentedColormap.from_list("suit", SEQ)
SSP_NAME = {"126": "SSP1-2.6", "245": "SSP2-4.5", "370": "SSP3-7.0", "585": "SSP5-8.5"}

plt.rcParams.update({"font.size": 8, "axes.edgecolor": GRAY, "axes.linewidth": 0.6, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.labelcolor": INK2, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "grid.color": "#e6e5e2", "grid.linewidth": 0.6, "pdf.fonttype": 42})


def us_boundary() -> gpd.GeoDataFrame:
    """US state boundaries, simplified to ~2 km so that the PDFs stay small."""
    g = gpd.read_file(ROOT / "data/data/US_shapefile/US_shapefile.shp").to_crs(4326)
    g["geometry"] = g.geometry.simplify(0.02, preserve_topology=True)
    return g


with rasterio.open(ROOT / "data/data/SSP_245/Bioclim_worldclim_average_2041_2060/Clipped/In_tiff_format/Bio1.tif") as _src:
    FUTURE_MASK = np.isfinite(_src.read(1))


def mean_raster(paths: list[Path]) -> tuple[np.ndarray, tuple]:
    arrs = []
    for p in paths:
        with rasterio.open(p) as src:
            a = src.read(1).astype("float64"); a[(a == src.nodata) | ~np.isfinite(a)] = np.nan; arrs.append(a)
            b = src.bounds
    m = np.nanmean(np.stack(arrs), axis=0)
    if m.shape == FUTURE_MASK.shape:
        m[~FUTURE_MASK] = np.nan  # same land cells in every period
    return m, (b.left, b.right, b.bottom, b.top)


def draw_map(ax, arr, extent, boundary, title, vmax=1.0):
    im = ax.imshow(arr, cmap=CMAP, vmin=0, vmax=vmax, extent=extent, interpolation="nearest")
    boundary.boundary.plot(ax=ax, color=INK2, linewidth=0.3)
    ax.set_title(title, fontsize=8, loc="left", color=INK)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    return im


def maps(results: Path) -> None:
    boundary = us_boundary()
    # Figures 4-5: baseline by m for CE and SM
    for species, code in [("Corn_Earworm", "CE"), ("Spongy_Moth", "SM")]:
        panels = []
        for m in ["0.0", "0.25", "0.5", "0.75", "1.0"]:
            paths = [Path(p) for p in glob.glob(f"{results}/SSP_245/{species}/{m}/lph/2.0/*/current.tif")]
            if paths:
                arr, ext = mean_raster(paths); panels.append((f"m = {float(m):g} (n = {len(paths)})", arr, ext))
        if not panels:
            continue
        # presence panel from one state
        st = sorted(glob.glob(f"{results}/SSP_245/{species}/0.25/lph/2.0/*/experiment_states.pkl"))
        pres = None
        if st:
            import joblib
            s = joblib.load(st[0]); pres = s["presence"].to_crs(4326); del s
        for tag, items in [("fig1", panels[:3]), ("fig2", panels[3:])]:
            n = len(items) + (1 if tag == "fig2" and pres is not None else 0)
            fig, axes = plt.subplots(1, n, figsize=(3.4 * n, 2.4), dpi=200)
            axes = np.atleast_1d(axes)
            for ax, (title, arr, ext) in zip(axes, items):
                im = draw_map(ax, arr, ext, boundary, title)
            if tag == "fig2" and pres is not None:
                ax = axes[-1]; boundary.boundary.plot(ax=ax, color=INK2, linewidth=0.3)
                ax.scatter(pres.geometry.x, pres.geometry.y, s=1.2, color=CAT[1], linewidths=0)
                ax.set_title(f"Thinned presences (n = {len(pres)})", fontsize=8, loc="left"); ax.set_xticks([]); ax.set_yticks([])
                for sp_ in ax.spines.values():
                    sp_.set_visible(False)
            cb = fig.colorbar(im, ax=list(axes), fraction=0.02, pad=0.02); cb.set_label("Relative climatic suitability (cloglog), mean of 20 fits", fontsize=7); cb.ax.tick_params(labelsize=6); cb.outline.set_visible(False)
            fig.savefig(FIGS / f"background_effect_predictions_{code}_{tag}.pdf", bbox_inches="tight"); plt.close(fig)
            print("wrote", f"background_effect_predictions_{code}_{tag}.pdf")
    # Figures 6-10: baseline / 2040 / 2060 under SSP2-4.5, thinned records on the
    # baseline panel, hatching where most fits extrapolate (a predictor outside
    # the training range of the fit)
    import joblib
    from maxent_insect_dir import config as _cfg
    for species, code in SP.items():
        runs = [str(Path(r).parent) for r in sorted(glob.glob(f"{results}/SSP_245/{species}/0.25/lph/2.0/*/experiment_states.pkl"))]
        files = {"Baseline 1970--2000": ("current.tif", None), "2021--2040, SSP2-4.5": ("2040.tif", "2021_2040"), "2041--2060, SSP2-4.5": ("2060.tif", "2041_2060")}
        panels = []
        for title, (f, period) in files.items():
            paths = [Path(r) / f for r in runs if (Path(r) / f).exists()]
            if paths and len(paths) == len(runs):
                arr, ext = mean_raster(paths); panels.append((title, arr, ext, period))
        if len(panels) < 3:
            print("skip maps for", code, "(incomplete)"); continue
        ranges, pres = [], None
        for r in runs:
            s_ = joblib.load(Path(r) / "experiment_states.pkl")
            ranges.append((list(s_["x_train"].columns), s_["x_train"].min(), s_["x_train"].max()))
            if pres is None:
                pres = s_["presence"].to_crs(4326)
            del s_
        novel = {}
        for _, _, _, period in panels[1:]:
            d = Path(_cfg.config_worldclim["SSP_245"][period]); count = None
            for cols, lo, hi in ranges:
                nov = None
                for c in cols:
                    if c == "elevation":
                        continue
                    with rasterio.open(d / f"{c}.tif") as src:
                        x = src.read(1).astype("float64")
                    m_ = np.isfinite(x) & ((x < lo[c]) | (x > hi[c]))
                    nov = m_ if nov is None else (nov | m_)
                count = nov.astype(int) if count is None else count + nov
            novel[period] = count / len(ranges)
        fig, axes = plt.subplots(1, 3, figsize=(10.5, 2.5), dpi=200)
        for i, (ax, (title, arr, ext, period)) in enumerate(zip(axes, panels)):
            im = draw_map(ax, arr, ext, boundary, f"{'ABC'[i]}) {title}".replace("--", "\u2013"))
            if period is None:
                ax.scatter(pres.geometry.x, pres.geometry.y, s=0.35, color=INK, linewidths=0, alpha=0.45, zorder=3)
            else:
                mask = np.where(np.isfinite(arr) & (novel[period] > 0.5), 1.0, np.nan)
                if np.isfinite(mask).any():
                    ny, nx = mask.shape; x0, x1, y0, y1 = ext
                    xs = np.linspace(x0, x1, nx + 1); ys = np.linspace(y1, y0, ny + 1)
                    with matplotlib.rc_context({"hatch.color": INK2, "hatch.linewidth": 0.3}):
                        ax.pcolor(xs, ys, np.ma.masked_invalid(mask), hatch="//////", facecolor="none", edgecolor="none", linewidth=0, zorder=2)
        if code == "CE":  # no corn earworm record west of 103 W: grey out the unsampled West
            for ax in axes:
                ax.axvspan(-125.5, -103.0, color="#9a9893", alpha=0.25, lw=0, zorder=2.5)
                ax.text(-114, 25.6, "no records", fontsize=6, color=INK2, ha="center", zorder=4)
        cb = fig.colorbar(im, ax=list(axes), fraction=0.02, pad=0.02)
        cb.set_label(f"Relative climatic suitability (cloglog), mean of {len(runs)} fits", fontsize=7); cb.ax.tick_params(labelsize=6); cb.outline.set_visible(False)
        fig.savefig(FIGS / "Predictions" / f"cuurent_future_predictions_{code}_new_fig.pdf", bbox_inches="tight"); plt.close(fig)
        share = {k: float(np.nanmean(np.where(np.isfinite(panels[0][1]), v > 0.5, np.nan))) for k, v in novel.items()}
        print("wrote", f"Predictions/cuurent_future_predictions_{code}_new_fig.pdf", "| land share hatched:", {k: round(100 * v, 1) for k, v in share.items()})


def drift(drift_root: Path) -> None:
    summ = pd.read_csv(drift_root / "drift_summary.csv"); imp = pd.read_csv(drift_root / "drift_importances.csv")
    summ["label"] = np.where(summ.condition == "drift", summ.level_km.map(lambda v: f"{v:g} km"), "Fresh draw")
    order = [f"{v:g} km" for v in sorted(summ.level_km.dropna().unique())] + ["Fresh draw"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.2), dpi=200, gridspec_kw={"width_ratios": [1, 1.4]})
    data = [summ.loc[summ.label == o, "spearman"].values for o in order]
    ticks = []
    for o in order:
        pc = summ.loc[summ.label == o, "frac_cell_changed"]
        ticks.append(f"{o}\n({100*pc.mean():.0f}%)" if pc.notna().any() else o)
    bp = ax1.boxplot(data, tick_labels=ticks, widths=0.45, patch_artist=True, medianprops=dict(color=INK, linewidth=1.2),
                     boxprops=dict(facecolor="#cde2fb", edgecolor=CAT[0], linewidth=0.8), whiskerprops=dict(color=CAT[0], linewidth=0.8),
                     capprops=dict(color=CAT[0], linewidth=0.8), flierprops=dict(marker="o", markersize=3, markerfacecolor=CAT[0], markeredgecolor="none"))
    ax1.set_xlabel("Displacement of background points (share of points in a new cell)"); ax1.set_ylabel("Spearman ρ with base importance"); ax1.yaxis.grid(True); ax1.set_axisbelow(True)
    ax1.set_title("A) Rank stability", loc="left", fontsize=8)
    base = imp[imp.condition == "base"].iloc[0]
    pred_cols = [c for c in imp.columns if c.startswith("Bio") or c == "elevation"]
    top6 = base[pred_cols].astype(float).sort_values(ascending=False).index[:6].tolist()
    imp["label"] = np.where(imp.condition == "drift", imp.level_km.map(lambda v: f"{v:g} km"), np.where(imp.condition == "base", "Base", "Fresh draw"))
    xorder = ["Base"] + order
    x = np.arange(len(xorder))
    for j, var in enumerate(top6):
        means = [imp.loc[imp.label == o, var].mean() for o in xorder]; sds = [imp.loc[imp.label == o, var].std() if o != "Base" else 0 for o in xorder]
        ax2.errorbar(x + (j - 2.5) * 0.06, means, yerr=sds, fmt="o-", ms=4, lw=1.2, color=CAT[j % len(CAT)], capsize=0, label=var, markeredgecolor="white", markeredgewidth=0.6)
    ax2.set_xticks(x); ax2.set_xticklabels(xorder); ax2.set_ylabel("Permutation importance (drop in AUC)"); ax2.set_xlabel("Condition")
    ax2.legend(frameon=False, ncol=6, fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.22), handlelength=1.5, columnspacing=1.0); ax2.yaxis.grid(True); ax2.set_axisbelow(True)
    ax2.set_title("B) Six leading predictors (mean ± SD)", loc="left", fontsize=8)
    fig.tight_layout(); fig.savefig(FIGS / "drift_replicated.pdf", bbox_inches="tight"); plt.close(fig); print("wrote drift_replicated.pdf")


def change(prefix: Path) -> None:
    """Figure 11: five-model mean (large marker) and each climate model (small symbols) per pathway."""
    summ = pd.read_csv(f"{prefix}_summary.csv", dtype={"ssp": str})
    s60 = summ[summ.period == "2041_2060"]
    species = ["BMSB", "CE", "SM", "RW", "SL"]
    ssp_col = {"126": "#86b6ef", "245": "#3987e5", "370": "#1c5cab", "585": "#0d366b"}  # ordered pathways: one-hue ramp
    gcm_mark = {"ACCESS-CM2": "D", "EC-Earth3-Veg": "^", "MIROC6": "v", "MPI-ESM1-2-HR": "s", "UKESM1-0-LL": "P"}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 3.8), dpi=200)
    for ax, metric, xlabel, scale in [(ax1, "pct_area_p10", "Change in P10 suitable area, 2041\u20132060 (%)", 1.0),
                                      (ax2, "d_centroid_lat_cont", "Shift of suitability-weighted centroid, 2041\u20132060 (km north)", 111.0)]:
        for i, ssp in enumerate(["126", "245", "370", "585"]):
            for k, sp in enumerate(species):
                y = k + (i - 1.5) * 0.18
                r = s60[(s60.species == sp) & (s60.ssp == ssp)]
                if r.empty:
                    continue
                vals = scale * r[f"{metric}_mean"].values
                ax.plot([vals.min(), vals.max()], [y, y], color=ssp_col[ssp], lw=1.0, alpha=0.6, zorder=2)
                for _, row in r.iterrows():
                    ax.scatter([scale * row[f"{metric}_mean"]], [y], s=15, marker=gcm_mark.get(row.gcm, "o"), facecolor="white",
                               edgecolor=ssp_col[ssp], linewidths=0.7, zorder=3)
                ax.scatter([vals.mean()], [y], s=34, color=ssp_col[ssp], edgecolor="white", linewidths=0.8, zorder=4)
        ax.axvline(0, color=GRAY, lw=0.8, zorder=1)
        ax.set_yticks(range(len(species))); ax.set_yticklabels(species); ax.invert_yaxis(); ax.set_xlabel(xlabel); ax.xaxis.grid(True); ax.set_axisbelow(True)
    ax1.set_title("A) Area", loc="left", fontsize=8); ax2.set_title("B) Position", loc="left", fontsize=8)
    from matplotlib.lines import Line2D
    h_ssp = [Line2D([], [], marker="o", ls="", color=c, markersize=5, label=SSP_NAME[k]) for k, c in ssp_col.items()]
    h_gcm = [Line2D([], [], marker=m_, ls="", markerfacecolor="white", markeredgecolor=INK2, markersize=5, label=g) for g, m_ in gcm_mark.items()]
    fig.legend(handles=h_ssp, frameon=False, fontsize=7, ncol=4, loc="lower center", bbox_to_anchor=(0.3, -0.04),
               title="Pathway: large dot = mean of the five climate models; line = range", title_fontsize=7)
    fig.legend(handles=h_gcm, frameon=False, fontsize=7, ncol=3, loc="lower center", bbox_to_anchor=(0.78, -0.07),
               title="Climate model (mean of 20 fits)", title_fontsize=7)
    fig.tight_layout(rect=(0, 0.13, 1, 1)); fig.savefig(FIGS / "change_summary.pdf", bbox_inches="tight"); plt.close(fig); print("wrote change_summary.pdf")


RAW_FILES = {"BMSB": "Brown_Marmorated_Stink_Bug_Halyomorpha_halys_1999_2023.gpkg", "CE": "Corn_Earworm_Helicoverpa_Zea_2004_2023.gpkg",
             "SM": "spongy_moth_(formerly_gypsy_moth)_(Lymantria_dispar).gpkg", "RW": "Root_Weevil_Diaprepes_abbreviatus_2012_2023.gpkg",
             "SL": "spotted_lanternfly_(Lycorma_delicatula).gpkg"}
REMOVED_STATES = {"SM": {"washington"}, "RW": {"alabama", "georgia", "mississippi", "south carolina"}}


def records() -> None:
    """Figure 1: all records (gray), records removed as outside the established range (orange),
    and the thinned records used by the models (blue), one panel per species."""
    boundary = us_boundary()
    out = FIGS / "presence_raw"; out.mkdir(parents=True, exist_ok=True)
    for folder, code in SP.items():
        raw = gpd.read_file(ROOT / "data/data/Species_Data/Clean_Data" / RAW_FILES[code]).to_crs(4326)
        gone = raw["state"].isin(REMOVED_STATES.get(code, set()))
        thin = pd.read_csv(ROOT / f"data_release/occurrences_{folder}.csv")
        fig, ax = plt.subplots(figsize=(3.3, 2.1), dpi=200)
        boundary.plot(ax=ax, color="#f3f2ef", edgecolor="#c9c7c1", linewidth=0.3)
        ax.scatter(raw.geometry.x[~gone], raw.geometry.y[~gone], s=0.6, color="#b3b1ab", linewidths=0, zorder=2,
                   label=(f"records kept ({int((~gone).sum()):,})" if gone.any() else f"records ({len(raw):,})"))
        ax.scatter(thin.lon, thin.lat, s=1.4, color=CAT[0], linewidths=0, zorder=3, label=f"after thinning ({len(thin):,})")
        if gone.any():
            ax.scatter(raw.geometry.x[gone], raw.geometry.y[gone], s=5, marker="x", color=CAT[1], linewidths=0.6, zorder=4,
                       label=f"removed ({int(gone.sum())})")
        ax.set_xlim(-125.5, -66.5); ax.set_ylim(24.3, 49.7); ax.set_xticks([]); ax.set_yticks([])
        for sp_ in ax.spines.values():
            sp_.set_visible(False)
        leg = ax.legend(loc="lower left", fontsize=5.5, frameon=False, markerscale=3, handletextpad=0.2, borderaxespad=0.1)
        fig.tight_layout(pad=0.1); fig.savefig(out / f"RAW_{code}.pdf", bbox_inches="tight"); plt.close(fig)
    print("wrote presence_raw/RAW_*.pdf")


def mcurves() -> None:
    """CBI and AUC against m for each species: main checkerboard over the contiguous US (mean +- SD),
    the exchanged checkerboard, and the three accessible areas."""
    t2 = pd.read_csv(ROOT / "docs/tables/table2_revision_stats.csv")
    sw = pd.read_csv(ROOT / "docs/tables/swap_twofold.csv")
    acc = pd.read_csv(ROOT / "docs/tables/accessible_area_results.csv")
    ms = [0.0, 0.25, 0.5, 0.75, 1.0]
    order = ["BMSB", "CE", "SM", "RW", "SL"]
    fig, axes = plt.subplots(2, 5, figsize=(9.6, 3.9), dpi=200, sharex=True)
    green, mk = CAT[2], {"eco": "o", "eco100": "s", "rec200": "^"}
    for j, code in enumerate(order):
        a = t2[t2.species == code].sort_values("m"); b = sw[sw.species == code].sort_values("m")
        for i, (metric, ylab) in enumerate((("cbi", "Test CBI"), ("auc", "Test AUC"))):
            ax = axes[i, j]
            for d in ("eco", "eco100", "rec200"):
                r = acc[(acc.species == code) & (acc.definition == d)].iloc[0]
                ax.plot(ms, [r[f"{metric}_{m}"] for m in ms], color=green, lw=0.8, alpha=0.8, marker=mk[d], ms=2.5, zorder=2,
                        label="inside accessible areas" if d == "eco" else None)
            if metric == "cbi":
                ax.fill_between(a.m, a.cbi_mean - a.cbi_sd, a.cbi_mean + a.cbi_sd, color=CAT[0], alpha=0.15, lw=0, zorder=1)
                ax.plot(b.m, b.cbi_B, color=CAT[1], lw=1.0, ls="--", marker="o", ms=2.5, zorder=3, label="contiguous US, folds exchanged")
            ax.plot(a.m, a[f"{metric}_mean"], color=CAT[0], lw=1.6, marker="o", ms=3, zorder=4, label="contiguous US")
            ax.set_xticks(ms); ax.set_xticklabels(["0", ".25", ".5", ".75", "1"]); ax.yaxis.grid(True); ax.set_axisbelow(True)
            if i == 0:
                ax.set_title(NAMES[code], fontsize=7.5, loc="left")
                ax.set_ylim(-0.2, 1.02)
            else:
                ax.set_ylim(0.45, 1.0); ax.set_xlabel("$m$")
            if j == 0:
                ax.set_ylabel(ylab)
    h, l = axes[0, 0].get_legend_handles_labels()
    h, l = h[::-1], l[::-1]  # contiguous US first
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, fontsize=7, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(FIGS / "m_curves.pdf", bbox_inches="tight"); plt.close(fig)
    print("wrote m_curves.pdf")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", nargs="?", default="all", choices=["maps", "drift", "change", "records", "mcurves", "all"])
    ap.add_argument("--results", default=str(ROOT / "runs/revision_main"))
    ap.add_argument("--drift-root", default=str(ROOT / "runs/revision_drift"))
    ap.add_argument("--proj", default=str(ROOT / "docs/tables/projections"))
    args = ap.parse_args()
    (FIGS / "Predictions").mkdir(parents=True, exist_ok=True)
    if args.what in ("maps", "all"):
        maps(Path(args.results))
    if args.what in ("drift", "all") and Path(args.drift_root, "drift_summary.csv").exists():
        drift(Path(args.drift_root))
    if args.what in ("change", "all") and Path(f"{args.proj}_summary.csv").exists():
        change(Path(args.proj))
    if args.what in ("records", "all"):
        records()
    if args.what in ("mcurves", "all") and (ROOT / "docs/tables/accessible_area_results.csv").exists():
        mcurves()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
