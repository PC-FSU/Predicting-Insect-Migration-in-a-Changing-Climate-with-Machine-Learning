#!/usr/bin/env python3
"""Print the numbers needed for the sentences of the revised manuscript.

Reads the CSV outputs of table2_stats.py, make_paper_tables.py,
analyze_projections.py, importance_table.py and drift_experiment.py and
prints short factual statements (best m per species, paired differences,
two-fold agreement, radius range, grid best, area and centroid changes,
threshold sign agreement, GCM decomposition, importance frequencies, drift
statistics). Nothing is written; copy the facts into the text by hand.

Usage: python scripts/summarize_for_text.py [--proj docs/tables/projections]
"""

from __future__ import annotations

import argparse
import os
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/tables"
ORDER = ["BMSB", "CE", "SM", "RW", "SL"]
SSP_NAME = {"126": "SSP1-2.6", "245": "SSP2-4.5", "370": "SSP3-7.0", "585": "SSP5-8.5"}


def section(title: str) -> None:
    print("\n" + "=" * 8 + " " + title + " " + "=" * 8)


def table2(prefix: Path) -> None:
    f = Path(f"{prefix}_stats.csv")
    if not f.exists():
        return
    d = pd.read_csv(f)
    section("Table 2: CBI vs m")
    for sp in ORDER:
        x = d[d.species == sp]
        if x.empty:
            continue
        best = x.loc[x.cbi_mean.idxmax()]
        r25 = x[x.m == 0.25].iloc[0]
        drop1 = x[x.m == 0.0].cbi_mean.iloc[0] - x[x.m == 1.0].cbi_mean.iloc[0] if (x.m == 1.0).any() else np.nan
        auc_range = x[x.m < 1].auc_mean.max() - x[x.m < 1].auc_mean.min()
        print(f"{sp}: best m = {best.m:.2f} (CBI {best.cbi_mean:.3f} ± {best.cbi_sd:.3f}); m=0.25 CBI {r25.cbi_mean:.3f} ± {r25.cbi_sd:.3f}; "
              f"CBI(m=1) {x[x.m==1.0].cbi_mean.iloc[0]:.3f}; AUC range for m<1 {auc_range:.3f} (max at m={x[x.m<1].loc[x[x.m<1].auc_mean.idxmax()].m:.2f}); "
              f"CBI at m=0 {x[x.m==0.0].cbi_mean.iloc[0]:.3f} with AUC {x[x.m==0.0].auc_mean.iloc[0]:.3f}")
        for _, r in x.iterrows():
            if r.m != 0.25:
                print(f"    vs m={r.m:.2f}: dCBI {r.delta_cbi:+.3f} [{r.ci_lo:+.3f}, {r.ci_hi:+.3f}], P(0.25 better) {r.p_ref_wins:.2f}")


def swap() -> None:
    f = DOCS / "swap_twofold.csv"
    if not f.exists():
        return
    d = pd.read_csv(f)
    section("Two-fold check")
    for sp in ORDER:
        x = d[d.species == sp]
        if x.empty:
            continue
        a, b = x.best_A.iloc[0], x.best_B.iloc[0]
        cbiB_at_a = x[x.m == a].cbi_B.iloc[0]; bestB_val = x[x.m == b].cbi_B.iloc[0]
        cbiA_at_b = x[x.m == b].cbi_A.iloc[0]; bestA_val = x[x.m == a].cbi_A.iloc[0]
        print(f"{sp}: best on A m={a:.2f}, best on B m={b:.2f} ({'same' if a == b else 'different'}); "
              f"m chosen on A gives CBI {cbiB_at_a:.3f} on B (best on B {bestB_val:.3f}, loss {bestB_val-cbiB_at_a:.3f}); "
              f"m chosen on B gives {cbiA_at_b:.3f} on A (best {bestA_val:.3f}, loss {bestA_val-cbiA_at_b:.3f})")


def radius() -> None:
    f = Path(os.environ.get("MAXENT_PAPER_DIR", str(ROOT / "Maxent_Paper/Maxent_Paper_MDPI_Insects_Revision2"))) / "tables/radius.tex"
    if f.exists() and "pending" not in f.read_text():
        section("Kernel radius (table rows)")
        print(f.read_text())


def grid() -> None:
    f = DOCS / "grid_best.csv"
    if not f.exists():
        return
    section("Feature x beta grid")
    d = pd.read_csv(f)
    for _, r in d.iterrows():
        print(f"{r.species}: best {str(r.best_feature).upper()} beta {r.best_beta:.1f} CBI {r.cbi_best:.3f} vs reference {r.cbi_ref:.3f} (gain {r.cbi_best - r.cbi_ref:+.3f})")


def projections(prefix: Path) -> None:
    f = Path(f"{prefix}_summary.csv")
    if not f.exists():
        return
    s = pd.read_csv(f, dtype={"ssp": str}); b = pd.read_csv(f"{prefix}_baseline.csv").set_index("species")
    acc = s[s.gcm == "ACCESS-CM2"]
    section("Projected changes (ACCESS-CM2, P10, 2041-2060)")
    for sp in ORDER:
        x = acc[(acc.species == sp) & (acc.period == "2041_2060")]
        if x.empty:
            continue
        rng = f"{x.pct_area_p10_mean.min():+.0f} to {x.pct_area_p10_mean.max():+.0f} %"
        ci_ex0 = int(((x.pct_area_p10_lo > 0) | (x.pct_area_p10_hi < 0)).sum())
        r245 = x[x.ssp == "245"].iloc[0]
        print(f"{sp}: baseline P10 share {100*b.loc[sp].share_p10:.1f} % ({b.loc[sp].area_p10/1e3:.0f} thousand km2); change 2041-2060 across SSPs {rng}; "
              f"CI excludes 0 in {ci_ex0}/4 pathways; SSP2-4.5: {r245.pct_area_p10_mean:+.0f} [{r245.pct_area_p10_lo:+.0f}, {r245.pct_area_p10_hi:+.0f}] % "
              f"(0.5 cut-off {r245.pct_area_05_mean:+.0f}, maxSSS {r245.pct_area_maxsss_mean:+.0f}); d mean suitability {r245.d_mean_suit_mean:+.3f}")
        print(f"    centroid (cont.) {111*r245.d_centroid_lat_cont_mean:+.0f} km [{111*r245.d_centroid_lat_cont_lo:+.0f}, {111*r245.d_centroid_lat_cont_hi:+.0f}]; "
              f"P10 centroid {111*r245.d_centroid_lat_bin_mean:+.0f}; trailing edge {111*r245.d_lat_p05_mean:+.0f} [{111*r245.d_lat_p05_lo:+.0f}, {111*r245.d_lat_p05_hi:+.0f}]; "
              f"leading edge {111*r245.d_lat_p95_mean:+.0f} [{111*r245.d_lat_p95_lo:+.0f}, {111*r245.d_lat_p95_hi:+.0f}]; baseline centroid {b.loc[sp].centroid_lat_cont:.1f} N")
        x40 = acc[(acc.species == sp) & (acc.period == "2021_2040")]
        if not x40.empty:
            print(f"    2021-2040 across SSPs {x40.pct_area_p10_mean.min():+.0f} to {x40.pct_area_p10_mean.max():+.0f} %")
    # threshold sign agreement
    section("Threshold sign agreement (SSP2-4.5, 2041-2060)")
    for sp in ORDER:
        x = acc[(acc.species == sp) & (acc.period == "2041_2060") & (acc.ssp == "245")]
        if x.empty:
            continue
        r = x.iloc[0]; signs = {k: np.sign(r[f"pct_area_{k}_mean"]) for k in ("05", "p10", "maxsss")}
        print(f"{sp}: signs {signs}; spread of the three estimates {max(r.pct_area_05_mean, r.pct_area_p10_mean, r.pct_area_maxsss_mean) - min(r.pct_area_05_mean, r.pct_area_p10_mean, r.pct_area_maxsss_mean):.0f} points; "
              f"baseline shares 0.5 {100*b.loc[sp].share_05:.1f} %, P10 {100*b.loc[sp].share_p10:.1f} %, maxSSS {100*b.loc[sp].share_maxsss:.1f} %")
    # centroid direction summary over all pathways
    section("Centroid direction over all SSPs, 2041-2060")
    for sp in ORDER:
        x = acc[(acc.species == sp) & (acc.period == "2041_2060")]
        if x.empty:
            continue
        print(f"{sp}: centroid shift {111*x.d_centroid_lat_cont_mean.min():+.0f} to {111*x.d_centroid_lat_cont_mean.max():+.0f} km; CI excludes 0 in {int(((x.d_centroid_lat_cont_lo > 0) | (x.d_centroid_lat_cont_hi < 0)).sum())}/4")
    g = Path(f"{prefix}_gcm_decomposition.csv")
    if g.exists():
        d = pd.read_csv(g, dtype={"ssp": str}); d = d[(d.metric == "pct_area_p10") & (d.period == "2041_2060")]
        section("GCM spread vs sampling spread (P10 area change, 2041-2060)")
        ratios = []
        for _, r in d.iterrows():
            means = json.loads(r.gcm_means); agree = sum(1 for v in means.values() if np.sign(v) == np.sign(r.grand_mean))
            ratios.append(r.sd_between_gcm / r.sd_within_gcm if r.sd_within_gcm else np.nan)
            print(f"{r.species} {SSP_NAME.get(r.ssp, r.ssp)}: mean {r.grand_mean:+.0f} %, SD between GCMs {r.sd_between_gcm:.0f}, SD within {r.sd_within_gcm:.0f}, sign agreement {agree}/{r.n_gcm}; {means}")
        print(f"ratio between/within: median {np.nanmedian(ratios):.1f}, range {np.nanmin(ratios):.1f}-{np.nanmax(ratios):.1f}")


def importance() -> None:
    f = DOCS / "importance_revision_BMSB_raw.csv"
    if not f.exists():
        return
    d = pd.read_csv(f, index_col=0).fillna(0.0); ranks = d.rank(axis=1, ascending=False, method="min")
    section("Importance BMSB (20 fits)")
    top = d.mean().sort_values(ascending=False)
    for v in top.index[:8]:
        print(f"{v}: mean {d[v].mean():.3f} ± {d[v].std():.3f} (range {d[v].min():.3f}-{d[v].max():.3f}); top3 {(ranks[v] <= 3).sum()}/{len(d)}; top5 {(ranks[v] <= 5).sum()}/{len(d)}; mean rank {ranks[v].mean():.1f}")
    print("first-ranked predictor per fit:", ranks.idxmin(axis=1).value_counts().to_dict())
    print("elevation rank:", ranks["elevation"].mean() if "elevation" in ranks else "n/a")


def drift() -> None:
    f = ROOT / "runs/revision_drift/drift_summary.csv"
    if not f.exists():
        return
    d = pd.read_csv(f)
    section("Drift")
    for lvl, g in d[d.condition == "drift"].groupby("level_km"):
        print(f"{lvl:g} km: cells changed {100*g.frac_cell_changed.mean():.0f} %, rho {g.spearman.mean():.3f} (min {g.spearman.min():.3f}), top3 overlap {g.top3_overlap.mean():.1f}, top1 same {g.top1_same.mean():.1f}, dropped {g.n_dropped.mean():.0f}")
    g = d[d.condition == "redraw"]
    print(f"fresh draws: rho {g.spearman.mean():.3f} ± {g.spearman.std():.3f} (min {g.spearman.min():.3f}), top3 overlap {g.top3_overlap.mean():.1f}, top1 same {g.top1_same.mean():.1f}")


def tex_table(name: str, title: str) -> None:
    f = Path(os.environ.get("MAXENT_PAPER_DIR", str(ROOT / "Maxent_Paper/Maxent_Paper_MDPI_Insects_Revision2"))) / "tables" / f"{name}.tex"
    if f.exists():
        section(title)
        print(f.read_text())


def background_counts(table2_csv: Path) -> None:
    f = Path(f"{table2_csv}.csv")
    if not f.exists():
        return
    d = pd.read_csv(f)
    section("Background points kept of 10,000 (all losses come from the kernel share: m = 0 keeps 10,000)")
    for sp in ORDER:
        x = d[d.species == sp]
        for m in sorted(x.m.unique()):
            y = x[x.m == m].n_background
            eff = (m * 10000 - (10000 - y)) / y
            print(f"{sp} m={m:.2f}: kept {y.min()}-{y.max()} (mean {y.mean():.0f}); effective kernel share {eff.min():.3f}-{eff.max():.3f}")
    r = d[d.m == 0.25].n_background; r1 = d[d.m == 1.0].n_background
    print(f"all species: m=0.25 kept {r.min()}-{r.max()}; m=1 kept {r1.min()}-{r1.max()}")


def dropped() -> None:
    f = DOCS / "dropped_by_m.csv"
    if not f.exists():
        return
    d = pd.read_csv(f)
    section("Predictors dropped by the correlation filter (number of fits of 20, by m)")
    for sp in ORDER:
        x = d[d.species == sp]
        if x.empty:
            continue
        piv = x.pivot(index="predictor", columns="m", values="n_dropped")
        print(sp); print(piv[(piv > 0).any(axis=1)].to_string())
    tot = d.groupby("predictor").agg(n=("n_fits", "sum"), k=("n_dropped", "sum"))
    print("dropped in every fit of every species:", tot[tot.k == tot.n].index.tolist())


def novelty_and_signs(prefix: Path) -> None:
    f = Path(f"{prefix}_summary.csv")
    if not f.exists():
        return
    s = pd.read_csv(f, dtype={"ssp": str}); acc = s[s.gcm == "ACCESS-CM2"]
    section("Novelty, ACCESS-CM2: % of land / % of future P10 area with a predictor outside the training range")
    for sp in ORDER:
        x = acc[acc.species == sp].sort_values(["period", "ssp"])
        print(sp, "; ".join(f"{r.period[-4:]} {SSP_NAME[r.ssp]}: {100*r.novel_share_mean:.1f} / {100*r.novel_share_in_p10_mean:.1f}" for _, r in x.iterrows()))
    section("Threshold sign agreement, ACCESS-CM2, every pathway and period (0.5 / P10 / maxSSS / mean suitability)")
    for sp in ORDER:
        for _, r in acc[acc.species == sp].sort_values(["period", "ssp"]).iterrows():
            v = [r.pct_area_05_mean, r.pct_area_p10_mean, r.pct_area_maxsss_mean]
            flag = "" if len({np.sign(round(x)) for x in v}) == 1 else "   <-- thresholds disagree in sign"
            print(f"{sp} {r.period} {SSP_NAME[r.ssp]}: {v[0]:+.0f} / {v[1]:+.0f} / {v[2]:+.0f} %, d mean suit {r.d_mean_suit_mean:+.3f}{flag}")
    g = Path(f"{prefix}_gcm_decomposition.csv")
    if g.exists():
        d = pd.read_csv(g, dtype={"ssp": str}); d = d[(d.metric == "pct_area_p10") & (d.period == "2041_2060")].copy()
        d["ratio"] = d.sd_between_gcm / d.sd_within_gcm
        section("Ratio of climate-model spread to sampling spread by species (P10 area, 2041-2060)")
        for sp in ORDER:
            x = d[d.species == sp]
            if not x.empty:
                print(f"{sp}: ratio {x.ratio.min():.1f}-{x.ratio.max():.1f}; SD between {x.sd_between_gcm.min():.0f}-{x.sd_between_gcm.max():.0f}; SD within {x.sd_within_gcm.min():.0f}-{x.sd_within_gcm.max():.0f}; five-model mean {x.grand_mean.min():+.0f} to {x.grand_mean.max():+.0f}")
        four = d[d.species != "RW"]
        print(f"four species: ratio {four.ratio.min():.1f}-{four.ratio.max():.1f} (median {four.ratio.median():.1f}); all five median {d.ratio.median():.1f}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--proj", default=str(DOCS / "projections"))
    ap.add_argument("--table2", default=str(DOCS / "table2_revision"))
    args = ap.parse_args()
    table2(Path(args.table2)); swap(); radius(); grid(); projections(Path(args.proj)); importance(); drift()
    background_counts(Path(args.table2)); dropped(); novelty_and_signs(Path(args.proj))
    for name, title in [("thinning", "Thinning table"), ("si_percell", "One record per cell (S8)"), ("si_allrecords", "All records (S7)"), ("grid", "Grid table"), ("shift", "Shift table")]:
        tex_table(name, title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
