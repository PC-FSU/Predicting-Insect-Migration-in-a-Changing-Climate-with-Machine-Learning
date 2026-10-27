#!/usr/bin/env python3
"""Build the LaTeX table bodies of the revised manuscript from the run outputs.

Writes <paper dir>/tables/<name>.tex (paper dir = $MAXENT_PAPER_DIR, default
Maxent_Paper/Maxent_Paper_MDPI_Insects_Revision2) (row bodies that
main.tex and SI.tex \\input) and docs/tables/*.csv. Each table is built only if
its inputs exist, so the script can be run while the run sets are still
finishing. Thresholds, areas and shifts come from scripts/analyze_projections.py
outputs (run that first with --out docs/tables/projections).

Usage:
    python scripts/make_paper_tables.py [--only thinning,table2,swap,radius,grid,projection,drift,importance,sm_unthinned,si]
"""

from __future__ import annotations

import argparse
import os
import re
import glob
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from table2_stats import load as load_metrics  # noqa: E402

PAPER = Path(os.environ.get("MAXENT_PAPER_DIR", str(ROOT / "Maxent_Paper/Maxent_Paper_MDPI_Insects_Revision2"))) / "tables"  # active version (Revision 2); Revision 1 is frozen
DOCS = ROOT / "docs/tables"
PY = str(ROOT / ".venv/bin/python")
SP = {"Brown_Marmorated_Stink_bug": "BMSB", "Corn_Earworm": "CE", "Spongy_Moth": "SM", "Root_Weevil": "RW", "Spotted_Lanternfly": "SL"}
ORDER = ["BMSB", "CE", "SM", "RW", "SL"]
RAW = {"BMSB": 13755, "CE": 45119, "SM": 203, "RW": 1107, "SL": 25193}
SSP_NAME = {"126": "SSP1-2.6", "245": "SSP2-4.5", "370": "SSP3-7.0", "585": "SSP5-8.5"}


def p10_area_change(state_paths: list[str], future_file: str = "2060.tif") -> np.ndarray:
    """Relative change (%) of the P10 suitable area between current.tif and a future raster, per fit."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from analyze_projections import cell_area_km2, read
    import rasterio
    out = []
    for sp in state_paths:
        run_dir = Path(sp).parent
        if not (run_dir / "current.tif").exists() or not (run_dir / future_file).exists():
            continue
        s = joblib.load(sp)
        t = float(np.percentile(s["model"].predict(s["x_train"][s["y_train"] == 1]), 10)); del s
        with rasterio.open(run_dir / "current.tif") as src:
            area = cell_area_km2(src)
        cur, fut = read(run_dir / "current.tif"), read(run_dir / future_file)
        land = np.isfinite(cur) & np.isfinite(fut)
        a0, a1 = area[land & (cur >= t)].sum(), area[land & (fut >= t)].sum()
        out.append(100.0 * (a1 - a0) / a0 if a0 > 0 else np.nan)
    return np.asarray(out, dtype=float)


_NEGZERO = re.compile(r"(?<![\d.])[-+]0(\.0+)?(?![\d.])")
_MINUS = re.compile(r"(?<![\w$\-])-(?=\d)")


def tidy(row: str) -> str:
    """Typeset numbers: no signed zeros, a real minus sign instead of a hyphen."""
    row = _NEGZERO.sub(lambda mo: "0" + (mo.group(1) or ""), row)
    return _MINUS.sub("$-$", row)


def write(name: str, rows: list[str]) -> None:
    PAPER.mkdir(parents=True, exist_ok=True)
    rows = [tidy(r) for r in rows]
    (PAPER / f"{name}.tex").write_text("\n".join(rows) + "\n")
    print(f"wrote tables/{name}.tex ({len(rows)} lines)")


def fmt(x: float, d: int = 3) -> str:
    return "--" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


def pm(m: float, s: float, d: int = 3) -> str:
    return f"{fmt(m, d)} $\\pm$ {fmt(s, d)}"


def ci(m: float, lo: float, hi: float, d: int = 1, sign: bool = True) -> str:
    if np.isnan(m):
        return "--"
    f = f"{{:+.{d}f}}" if sign else f"{{:.{d}f}}"
    return f"{f.format(m)} [{f.format(lo)}, {f.format(hi)}]"


# ----------------------------------------------------------------------------
def thinning(main_root: Path) -> None:
    import rasterio
    sys.path.insert(0, str(ROOT / "MaxEnt_insect_dir"))
    import os
    os.environ.setdefault("MAXENT_DATA_ROOT", str(ROOT / "data"))
    import geopandas as gpd
    from maxent_insect_dir import config, utils

    ras = ROOT / "data/data/Bioclim_worldclim_average_1970_2000/wc2.1_10m_bio/Clipped/In_tiff_format/Bio1.tif"
    rows = []
    for species, code in SP.items():
        states = sorted(glob.glob(f"{main_root}/SSP_245/{species}/0.25/lph/2.0/*/experiment_states.pkl"))
        if not states:
            continue
        s = joblib.load(states[0])
        pres = s["presence"]; ntr, nte = int(s["y_train"].sum()), int(s["y_test"].sum()); del s
        g = gpd.read_file(config.Insect_list[species])[["geometry"]]
        thinned = len(utils.spatial_thinning(g, 10000))
        ll = pres.to_crs(4326)
        with rasterio.open(ras) as src:
            r, c = rasterio.transform.rowcol(src.transform, ll.geometry.x.values, ll.geometry.y.values)
        cells = len(set(zip(r, c)))
        rows.append(f"{code} & {len(g):,} & {thinned:,} & {len(pres):,} & {cells:,} & {ntr:,} & {nte:,} & {len(pres) - ntr - nte} \\\\")
    write("thinning", rows)


def table2(main_root: Path) -> None:
    out = DOCS / "table2_revision"
    subprocess.run([PY, str(ROOT / "scripts/table2_stats.py"), "--results", str(main_root), "--beta", "2.0", "--out", str(out)], check=True, capture_output=True)
    (PAPER / "table2_main.tex").write_text("\n".join(tidy(r) for r in Path(f"{out}.tex").read_text().splitlines()) + "\n")
    print("wrote tables/table2_main.tex")


def swap(main_root: Path, swap_root: Path) -> None:
    a = load_metrics(main_root, "lph", "2.0", "SSP_245"); b = load_metrics(swap_root, "lph", "2.0", "SSP_245")
    ma = a.groupby(["species", "m"]).cbi.agg(["mean", "std"]); mb = b.groupby(["species", "m"]).cbi.agg(["mean", "std"])
    rows, recs = [], []
    for sp in ORDER:
        if sp not in ma.index.get_level_values(0) or sp not in mb.index.get_level_values(0):
            continue
        xa, xb = ma.loc[sp], mb.loc[sp]
        best_a, best_b = float(xa["mean"].idxmax()), float(xb["mean"].idxmax())
        for i, m in enumerate(sorted(xa.index)):
            n_m = len(xa.index)
            extra = (f"\\multirow{{{n_m}}}{{*}}{{{best_a:.2f}}} & \\multirow{{{n_m}}}{{*}}{{{fmt(xb.loc[best_a, 'mean'])}}} & \\multirow{{{n_m}}}{{*}}{{{best_b:.2f}}} & \\multirow{{{n_m}}}{{*}}{{{fmt(xa.loc[best_b, 'mean'])}}}" if i == 0 else "& & &")
            rows.append(f"{sp} & {m:.2f} & {pm(xa.loc[m, 'mean'], xa.loc[m, 'std'])} & {pm(xb.loc[m, 'mean'], xb.loc[m, 'std']) if m in xb.index else '--'} & {extra} \\\\")
            recs.append(dict(species=sp, m=m, cbi_A=xa.loc[m, "mean"], sd_A=xa.loc[m, "std"], cbi_B=xb.loc[m, "mean"] if m in xb.index else np.nan, best_A=best_a, best_B=best_b))
        rows.append("\\midrule")
    write("swap", rows[:-1]); pd.DataFrame(recs).to_csv(DOCS / "swap_twofold.csv", index=False)


def radius(main_root: Path, r80: Path, r320: Path) -> None:
    sets = {}
    for name, root in [("80", r80), ("160", main_root), ("320", r320)]:
        try:
            d = load_metrics(root, "lph", "2.0", "SSP_245"); sets[name] = d.groupby(["species", "m"]).cbi.agg(["mean", "std"])
        except SystemExit:
            print("missing", root)
    if len(sets) < 2:
        return
    rows = []
    for sp in ORDER:
        for m in (0.25, 0.5, 0.75):
            cells, means = [], []
            for name in ("80", "160", "320"):
                if name in sets and (sp, m) in sets[name].index:
                    r = sets[name].loc[(sp, m)]; cells.append(pm(r["mean"], r["std"])); means.append(r["mean"])
                else:
                    cells.append("--")
            rng = f"{max(means) - min(means):.3f}" if len(means) > 1 else "--"
            rows.append(f"{sp} & {m:.2f} & " + " & ".join(cells) + f" & {rng} \\\\")
        rows.append("\\midrule")
    write("radius", rows[:-1])


def grid(grid_root: Path, main_root: Path, proj_prefix: Path) -> None:
    rows = []
    recs = []
    for species, code in SP.items():
        vals = []
        for p in glob.glob(f"{grid_root}/SSP_245/{species}/0.25/*/*/*/experiment_states.pkl"):
            parts = Path(p).parts; feat, beta = parts[-4], parts[-3]
            s = joblib.load(p); vals.append(dict(feature=feat, beta=beta, cbi=float(s["cbi_test"]["Spearman.cor"]))); del s
        if not vals:
            continue
        d = pd.DataFrame(vals).groupby(["feature", "beta"]).cbi.agg(["mean", "std", "size"]).reset_index()
        d.to_csv(DOCS / f"grid_{code}.csv", index=False)
        best = d.loc[d["mean"].idxmax()]
        ref = d[(d.feature == "lph") & (d.beta.astype(float) == 2.0)]
        ref_cbi = f"{ref['mean'].iloc[0]:.3f}" if len(ref) else "--"
        # area change (P10, SSP2-4.5, 2041-2060) for the best setting, from its own grid runs
        d_ref = "--"
        best_states = sorted(glob.glob(f"{grid_root}/SSP_245/{species}/0.25/{best.feature}/{best.beta}/*/experiment_states.pkl"))
        ch = p10_area_change(best_states)
        d_best = pm(np.nanmean(ch), np.nanstd(ch, ddof=1), 1) if len(ch) > 1 else "--"
        summ = proj_prefix.parent / f"{proj_prefix.name}_summary.csv"
        if summ.exists():
            c = pd.read_csv(summ); cr = c[(c.species == code) & (c.gcm == "ACCESS-CM2") & (c.ssp == 245) & (c.period == "2041_2060")]
            if len(cr):
                d_ref = pm(cr.pct_area_p10_mean.iloc[0], cr.pct_area_p10_sd.iloc[0], 1)
        rows.append(f"{code} & {best.feature.upper()} & {float(best.beta):.1f} & {best['mean']:.3f} & {ref_cbi} & {d_best} & {d_ref} \\\\")
        recs.append(dict(species=code, best_feature=best.feature, best_beta=float(best.beta), cbi_best=best["mean"], cbi_ref=ref["mean"].iloc[0] if len(ref) else np.nan,
                         d_area_best=np.nanmean(ch) if len(ch) else np.nan, n_best=len(ch)))
    if rows:
        write("grid", rows); pd.DataFrame(recs).to_csv(DOCS / "grid_best.csv", index=False)


def projection_tables(prefix: Path) -> None:
    summ_f, base_f = Path(f"{prefix}_summary.csv"), Path(f"{prefix}_baseline.csv")
    if not summ_f.exists():
        print("no projection summary yet"); return
    summ = pd.read_csv(summ_f, dtype={"ssp": str}); base = pd.read_csv(base_f).set_index("species")
    acc = summ[summ.gcm == "ACCESS-CM2"]
    # coverage: baseline area + % change per ssp x period
    rows = []
    for sp in ORDER:
        if sp not in base.index:
            continue
        b = base.loc[sp]
        cells = [f"{b.area_p10/1000:.0f}"]
        for ssp in ("126", "245", "370", "585"):
            for period in ("2021_2040", "2041_2060"):
                r = acc[(acc.species == sp) & (acc.ssp == ssp) & (acc.period == period)]
                cells.append(ci(r.pct_area_p10_mean.iloc[0], r.pct_area_p10_lo.iloc[0], r.pct_area_p10_hi.iloc[0], 0) if len(r) else "--")
        rows.append(f"{sp} & " + " & ".join(cells) + " \\\\")
    write("coverage", rows)
    # threshold sensitivity, SSP2-4.5 2041-2060
    rows = []
    for sp in ORDER:
        if sp not in base.index:
            continue
        b = base.loc[sp]; r = acc[(acc.species == sp) & (acc.ssp == "245") & (acc.period == "2041_2060")]
        if not len(r):
            continue
        r = r.iloc[0]
        rows.append(f"{sp} & {100*b.share_05:.1f} & {ci(r.pct_area_05_mean, r.pct_area_05_lo, r.pct_area_05_hi, 0)} & {100*b.share_p10:.1f} & {ci(r.pct_area_p10_mean, r.pct_area_p10_lo, r.pct_area_p10_hi, 0)} & {100*b.share_maxsss:.1f} & {ci(r.pct_area_maxsss_mean, r.pct_area_maxsss_lo, r.pct_area_maxsss_hi, 0)} & {ci(r.d_mean_suit_mean, r.d_mean_suit_lo, r.d_mean_suit_hi, 3)} \\\\")
    write("threshold", rows)
    # shift table (km)
    rows = []
    for sp in ORDER:
        if sp not in base.index:
            continue
        b = base.loc[sp]; r = acc[(acc.species == sp) & (acc.ssp == "245") & (acc.period == "2041_2060")]
        if not len(r):
            continue
        r = r.iloc[0]; k = 111.0
        pc = lambda c: f"{100*r[c + '_mean']:.0f}" if (c + "_mean") in r.index and np.isfinite(r[c + "_mean"]) else "--"  # noqa: E731
        rows.append(f"{sp} & {b.centroid_lat_cont:.1f} & {ci(k*r.d_centroid_lat_cont_mean, k*r.d_centroid_lat_cont_lo, k*r.d_centroid_lat_cont_hi, 0)} & {ci(k*r.d_centroid_lat_bin_mean, k*r.d_centroid_lat_bin_lo, k*r.d_centroid_lat_bin_hi, 0)} & {ci(k*r.d_lat_p05_mean, k*r.d_lat_p05_lo, k*r.d_lat_p05_hi, 0)} & {ci(k*r.d_lat_p95_mean, k*r.d_lat_p95_lo, k*r.d_lat_p95_hi, 0)} & {pc('retained_share')} & {pc('new_share')} & {pc('novel_share_in_p10')} \\\\")
    write("shift", rows)
    # gcm decomposition
    dec_f = Path(f"{prefix}_gcm_decomposition.csv")
    if dec_f.exists():
        dec = pd.read_csv(dec_f, dtype={"ssp": str}); rows = []
        for sp in ORDER:
            for ssp in ("126", "245", "370", "585"):
                r = dec[(dec.species == sp) & (dec.ssp == ssp) & (dec.period == "2041_2060") & (dec.metric == "pct_area_p10")]
                a = acc[(acc.species == sp) & (acc.ssp == ssp) & (acc.period == "2041_2060")]
                if not len(r):
                    continue
                r = r.iloc[0]; import json; means = json.loads(r.gcm_means); signs = sum(1 for v in means.values() if np.sign(v) == np.sign(r.grand_mean))
                rows.append(f"{sp} & {SSP_NAME[ssp]} & {r.grand_mean:+.0f} & {r.sd_between_gcm:.0f} & {r.sd_within_gcm:.0f} & {signs}/{r.n_gcm} & {a.pct_area_p10_mean.iloc[0]:+.0f} \\\\")
            rows.append("\\midrule")
        write("gcm", rows[:-1])


def drift(drift_root: Path) -> None:
    f = drift_root / "drift_summary.csv"
    if not f.exists():
        return
    d = pd.read_csv(f)
    d["label"] = np.where(d.condition == "drift", d.level_km.map(lambda v: f"Drift {v:g} km"), "Fresh draw")
    rows = []
    for label in [f"Drift {v:g} km" for v in sorted(d.level_km.dropna().unique())] + ["Fresh draw"]:
        g = d[d.label == label]
        if not len(g):
            continue
        pc = pm(100 * g.frac_cell_changed.mean(), 100 * g.frac_cell_changed.std(), 1) if g.frac_cell_changed.notna().any() else "--"
        rows.append(f"{label} & {pc} & {pm(g.spearman.mean(), g.spearman.std())} & {pm(g.kendall.mean(), g.kendall.std())} & {pm(g.top3_overlap.mean(), g.top3_overlap.std(), 1)} & {pm(g.top5_overlap.mean(), g.top5_overlap.std(), 1)} & {pm(g.cbi.mean(), g.cbi.std())} \\\\")
    write("drift", rows)


def sm_unthinned(main_root: Path, sm_root: Path) -> None:
    """Spongy moth: CBI/AUC by m with the records thinned (main set) and unthinned (as submitted)."""
    try:
        a = load_metrics(main_root, "lph", "2.0", "SSP_245"); b = load_metrics(sm_root, "lph", "2.0", "SSP_245")
    except SystemExit:
        print("sm_unthinned: inputs missing"); return
    a = a[a.species == "SM"].groupby("m").agg(cbi=("cbi", "mean"), cbi_sd=("cbi", "std"), auc=("auc", "mean"), n=("cbi", "size"))
    b = b[b.species == "SM_all"].groupby("m").agg(cbi=("cbi", "mean"), cbi_sd=("cbi", "std"), auc=("auc", "mean"), n=("cbi", "size"))
    rows = []
    for m in sorted(set(a.index) | set(b.index)):
        ra = a.loc[m] if m in a.index else None; rb = b.loc[m] if m in b.index else None
        rows.append(f"{m:.2f} & {pm(ra.cbi, ra.cbi_sd) if ra is not None else '--'} & {fmt(ra.auc) if ra is not None else '--'} & {pm(rb.cbi, rb.cbi_sd) if rb is not None else '--'} & {fmt(rb.auc) if rb is not None else '--'} \\\\")
    write("si_sm_unthinned", rows)


def si_allrecords(main_root: Path, all_root: Path, var_root: Path = ROOT / "runs/revision_rw_fltxca") -> None:
    """Table S6: established-range records (main set) versus all records for SM and RW, and for RW
    also the first revision filter (Florida, Texas, California only) from runs/revision_rw_fltxca."""
    try:
        a = load_metrics(main_root, "lph", "2.0", "SSP_245"); b = load_metrics(all_root, "lph", "2.0", "SSP_245")
    except SystemExit:
        print("si_allrecords: inputs missing"); return
    try:
        v = load_metrics(var_root, "lph", "2.0", "SSP_245")
    except SystemExit:
        v = pd.DataFrame(columns=["species", "m", "cbi"])
    rows = []
    for code, sp_main, sp_all, sp_var in [("SM", "Spongy_Moth", "Spongy_Moth_all", None),
                                          ("RW", "Root_Weevil", "Root_Weevil_all", "Root_Weevil_FL_TX_CA")]:
        ga = a[a.species == code].groupby("m").cbi.agg(["mean", "std"]); gb = b[b.species == f"{code}_all"].groupby("m").cbi.agg(["mean", "std"])
        gv = v[v.species == "RW_FLTXCA"].groupby("m").cbi.agg(["mean", "std"]) if sp_var else pd.DataFrame(columns=["mean", "std"])
        ch_a = p10_area_change(sorted(glob.glob(f"{main_root}/SSP_245/{sp_main}/0.25/lph/2.0/*/experiment_states.pkl")))
        ch_b = p10_area_change(sorted(glob.glob(f"{all_root}/SSP_245/{sp_all}/0.25/lph/2.0/*/experiment_states.pkl")))
        ch_v = p10_area_change(sorted(glob.glob(f"{var_root}/SSP_245/{sp_var}/0.25/lph/2.0/*/experiment_states.pkl"))) if sp_var else np.array([])
        for i, m in enumerate(sorted(set(ga.index) | set(gb.index))):
            def dch(ch):
                return pm(np.nanmean(ch), np.nanstd(ch, ddof=1), 0) if (m == 0.25 and len(ch) > 1) else ""
            ca = pm(ga.loc[m, "mean"], ga.loc[m, "std"]) if m in ga.index else "--"
            cb = pm(gb.loc[m, "mean"], gb.loc[m, "std"]) if m in gb.index else "--"
            cv = pm(gv.loc[m, "mean"], gv.loc[m, "std"]) if m in gv.index else "--"
            dv = dch(ch_v) if sp_var else ("--" if m == 0.25 else "")
            rows.append(f"{code if i == 0 else ''} & {m:.2f} & {ca} & {cb} & {cv} & {dch(ch_a)} & {dch(ch_b)} & {dv} \\\\")
        rows.append("\\midrule")
    write("si_allrecords", rows[:-1])


def si_percell(main_root: Path, cell_root: Path) -> None:
    """Table S7: 10 km thinning versus one record per climate cell (BMSB, RW, SL; m = 0.25)."""
    rows = []
    for species, code in [("Brown_Marmorated_Stink_bug", "BMSB"), ("Root_Weevil", "RW"), ("Spotted_Lanternfly", "SL")]:
        cells = []
        for root in (main_root, cell_root):
            st = sorted(glob.glob(f"{root}/SSP_245/{species}/0.25/lph/2.0/*/experiment_states.pkl"))
            if not st:
                cells.append(None); continue
            cbi, n = [], None
            for p in st:
                s = joblib.load(p); cbi.append(float(s["cbi_test"]["Spearman.cor"])); n = len(s["presence"]); del s
            ch = p10_area_change(st)
            cells.append((n, np.mean(cbi), np.std(cbi, ddof=1), np.nanmean(ch), np.nanstd(ch, ddof=1), len(st)))
        if cells[1] is None:
            continue
        a, b = cells
        rows.append(f"{code} & {a[0]:,} & {b[0]:,} & {pm(a[1], a[2])} & {pm(b[1], b[2])} & {pm(a[3], a[4], 0)} & {pm(b[3], b[4], 0)} \\\\")
    write("si_percell", rows)


def importance(main_root: Path) -> None:
    out = DOCS / "importance_revision"
    subprocess.run([PY, str(ROOT / "scripts/importance_table.py"), "--results", str(main_root), "--beta", "2.0", "--m", "0.25", "--species", "Brown_Marmorated_Stink_bug", "--out", str(out)], check=True, capture_output=True)
    (PAPER / "importance_bmsb.tex").write_text("\n".join(tidy(r) for r in Path(f"{out}.tex").read_text().replace("% Brown_Marmorated_Stink_bug\n", "").splitlines()) + "\n")
    print("wrote tables/importance_bmsb.tex")
    out_all = DOCS / "importance_revision_all"
    subprocess.run([PY, str(ROOT / "scripts/importance_table.py"), "--results", str(main_root), "--beta", "2.0", "--m", "0.25", "--all-species", "--top", "8", "--out", str(out_all)], check=True, capture_output=True)
    body = Path(f"{out_all}.tex").read_text().rstrip("\n")
    if body.endswith("\\midrule"):
        body = body[: -len("\\midrule")].rstrip("\n")
    (PAPER / "si_importance_all.tex").write_text(body + "\n")
    print("wrote tables/si_importance_all.tex")


def si_tables(main_root: Path, prefix: Path) -> None:
    # Table R1 of the response letter: submitted-sweep reproduction (unseeded beta 2.0) if present
    sub = DOCS / "table2_submitted_rerun.tex"
    if sub.exists():
        (PAPER / "si_table2_submitted.tex").write_text("\n".join(tidy(r) for r in sub.read_text().splitlines()) + "\n")
    # S1: predictors dropped by the correlation filter, per species and m
    # (the filter is computed on presences plus the training background, so the set depends on m)
    ALL = [f"Bio{i}" for i in range(1, 20)] + ["elevation"]
    rows, recs = [], []
    for species, code in SP.items():
        first = True
        for m in ("0.0", "0.25", "0.5", "0.75", "1.0"):
            states = glob.glob(f"{main_root}/SSP_245/{species}/{m}/lph/2.0/*/experiment_states.pkl")
            if not states:
                continue
            cnt = {v: 0 for v in ALL}
            for p in states:
                s = joblib.load(p); kept = set(s["cols_to_keep"]); del s
                for v in ALL:
                    if v not in kept:
                        cnt[v] += 1
            n = len(states)
            recs += [dict(species=code, m=float(m), predictor=v, n_fits=n, n_dropped=c) for v, c in cnt.items()]
            always = [v for v, c in cnt.items() if c == n]
            some = [f"{v} ({c})" for v, c in cnt.items() if 0 < c < n]
            txt = ", ".join(always) + ("; " if always and some else "") + ", ".join(some)
            rows.append(f"{code if first else ''} & {float(m):.2f} & {n} & {txt} \\\\")
            first = False
        if not first:
            rows.append("\\midrule")
    write("si_dropped", rows[:-1] if rows and rows[-1] == "\\midrule" else rows)
    pd.DataFrame(recs).to_csv(DOCS / "dropped_by_m.csv", index=False)
    # S2: thresholds
    base_f = Path(f"{prefix}_baseline.csv")
    if base_f.exists():
        base = pd.read_csv(base_f).set_index("species")
        rows = [f"{sp} & {base.loc[sp].t_p10:.3f} & {base.loc[sp].t_maxsss:.3f} \\\\" for sp in ORDER if sp in base.index]
        write("si_thresholds", rows)
    # S4: P10 area change and centroid shift for every climate model, pathway and period
    summ_f = Path(f"{prefix}_summary.csv")
    if summ_f.exists():
        summ = pd.read_csv(summ_f, dtype={"ssp": str})
        gcm_order = ["ACCESS-CM2"] + sorted(g for g in summ.gcm.unique() if g != "ACCESS-CM2")
        for period, name in (("2041_2060", "si_changes_2060"), ("2021_2040", "si_changes_2040")):
            rows = []
            for sp in ORDER:
                for j, gcm in enumerate(gcm_order):
                    cells = []
                    for ssp in ("126", "245", "370", "585"):
                        r = summ[(summ.species == sp) & (summ.gcm == gcm) & (summ.ssp == ssp) & (summ.period == period)]
                        cells += [f"{r.pct_area_p10_mean.iloc[0]:+.0f}", f"{111*r.d_centroid_lat_cont_mean.iloc[0]:+.0f}"] if len(r) else ["--", "--"]
                    rows.append(f"{sp if j == 0 else ''} & {gcm} & " + " & ".join(cells) + " \\\\")
                rows.append("\\midrule")
            write(name, rows[:-1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default=None)
    ap.add_argument("--main", default=str(ROOT / "runs/revision_main"))
    ap.add_argument("--swap", default=str(ROOT / "runs/revision_swap"))
    ap.add_argument("--r80", default=str(ROOT / "runs/revision_radius80"))
    ap.add_argument("--r320", default=str(ROOT / "runs/revision_radius320"))
    ap.add_argument("--grid", default=str(ROOT / "runs/revision_grid"))
    ap.add_argument("--drift", default=str(ROOT / "runs/revision_drift"))
    ap.add_argument("--proj", default=str(DOCS / "projections"))
    args = ap.parse_args()
    only = set(args.only.split(",")) if args.only else None
    DOCS.mkdir(parents=True, exist_ok=True)
    steps = {
        "thinning": lambda: thinning(Path(args.main)),
        "table2": lambda: table2(Path(args.main)),
        "swap": lambda: swap(Path(args.main), Path(args.swap)),
        "radius": lambda: radius(Path(args.main), Path(args.r80), Path(args.r320)),
        "grid": lambda: grid(Path(args.grid), Path(args.main), Path(args.proj)),
        "projection": lambda: projection_tables(Path(args.proj)),
        "drift": lambda: drift(Path(args.drift)),
        "importance": lambda: importance(Path(args.main)),
        "sm_unthinned": lambda: sm_unthinned(Path(args.main), Path(ROOT / "runs/revision_sm_unthinned")),
        "allrecords": lambda: si_allrecords(Path(args.main), Path(ROOT / "runs/revision_allrecords")),
        "percell": lambda: si_percell(Path(args.main), Path(ROOT / "runs/revision_percell")),
        "si": lambda: si_tables(Path(args.main), Path(args.proj)),
    }
    for name, fn in steps.items():
        if only and name not in only:
            continue
        try:
            fn()
        except SystemExit as e:
            print(f"[{name}] skipped: {e}")
        except FileNotFoundError as e:
            print(f"[{name}] skipped: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
