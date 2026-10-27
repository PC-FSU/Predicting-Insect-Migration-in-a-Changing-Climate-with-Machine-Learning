#!/usr/bin/env python3
"""Performance table with uncertainty: CBI and AUC versus m, plus bootstrap CIs.

Reads every experiment_states.pkl under a results root for one feature string
and beta, and writes (a) the mean ± SD table, (b) for every species the
difference in CBI between each m and the reference m (0.25 by default) with a
bootstrap 95 % confidence interval, and (c) the share of repeats in which the
reference m scored higher. Repeats that share a seed are paired; otherwise the
bootstrap is on the two independent samples.

Usage:
    python scripts/table2_stats.py --results runs/revision_main --beta 2.0 \
        --out docs/tables/table2_revision
"""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

SPECIES = {
    "Brown_Marmorated_Stink_bug": "BMSB",
    "Corn_Earworm": "CE",
    "Spongy_Moth": "SM",
    "Root_Weevil": "RW",
    "Spotted_Lanternfly": "SL",
    "Spooted_Lanternfly": "SL",
    "Spongy_Moth_all": "SM_all",
    "Root_Weevil_all": "RW_all",
    "Root_Weevil_FL_TX_CA": "RW_FLTXCA",
}
M_ORDER = ["0.0", "0.25", "0.5", "0.75", "1.0"]


def load(results: Path, feature: str, beta: str, pathway: str) -> pd.DataFrame:
    rows = []
    for species in SPECIES:
        for m in ("0", "0.0", "0.25", "0.5", "0.50", "0.75", "1", "1.0"):
            base = results / pathway / species / m / feature / beta
            for path in sorted(glob.glob(str(base / "*" / "experiment_states.pkl"))):
                s = joblib.load(path)
                rows.append(
                    {
                        "species": SPECIES[species],
                        "m": float(m),
                        "seed": s.get("seed"),
                        "repeat": s.get("repeat_index"),
                        "cbi": float(s["cbi_test"]["Spearman.cor"]),
                        "auc": float(s["auc"]["AUC_test"]),
                        "n_presence_train": int(s["y_train"].sum()),
                        "n_presence_test": int(s["y_test"].sum()),
                        "n_background": int(len(s["background"])),
                        "path": path,
                    }
                )
                del s
    df = pd.DataFrame(rows)
    if df.empty:
        raise SystemExit(f"no states under {results} for {feature}/{beta}")
    return df


def boot_ci(diff_samples: np.ndarray, n_boot: int, rng: np.random.Generator) -> tuple[float, float]:
    idx = rng.integers(0, len(diff_samples), size=(n_boot, len(diff_samples)))
    means = diff_samples[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def boot_ci_unpaired(a: np.ndarray, b: np.ndarray, n_boot: int, rng: np.random.Generator) -> tuple[float, float]:
    ia = rng.integers(0, len(a), size=(n_boot, len(a)))
    ib = rng.integers(0, len(b), size=(n_boot, len(b)))
    d = a[ia].mean(axis=1) - b[ib].mean(axis=1)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default="runs/paper_m_table")
    ap.add_argument("--feature", default="lph")
    ap.add_argument("--beta", default="2.0")
    ap.add_argument("--pathway", default="SSP_245")
    ap.add_argument("--reference-m", type=float, default=0.25)
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--out", default=None, help="output prefix (writes <out>.csv, <out>_summary.md, <out>.tex)")
    args = ap.parse_args()

    rng = np.random.default_rng(12345)
    df = load(Path(args.results), args.feature, args.beta, args.pathway)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(f"{args.out}.csv", index=False)

    summary = (
        df.groupby(["species", "m"])
        .agg(n=("cbi", "size"), cbi_mean=("cbi", "mean"), cbi_sd=("cbi", "std"), auc_mean=("auc", "mean"), auc_sd=("auc", "std"))
        .reset_index()
    )

    lines = [f"# CBI and AUC versus m ({args.results}, {args.feature}, beta {args.beta})", ""]
    lines.append("| species | m | n | CBI mean ± SD | AUC mean ± SD | ΔCBI vs m=%.2f [95%% CI] | P(ref > m) |" % args.reference_m)
    lines.append("|---|---|---|---|---|---|---|")
    tex = []
    stats_rows = []
    for sp in ["BMSB", "CE", "SM", "RW", "SL"]:
        d = df[df.species == sp]
        if d.empty:
            continue
        ref = d[d.m == args.reference_m].sort_values("seed")
        for m in sorted(d.m.unique()):
            cur = d[d.m == m].sort_values("seed")
            row = summary[(summary.species == sp) & (summary.m == m)].iloc[0]
            if m == args.reference_m or ref.empty:
                delta, lo, hi, pwin = np.nan, np.nan, np.nan, np.nan
            else:
                paired = (
                    ref.seed.notna().all() and cur.seed.notna().all() and len(ref) == len(cur) and (ref.seed.values == cur.seed.values).all()
                )
                if paired:
                    diff = ref.cbi.values - cur.cbi.values
                    delta = float(diff.mean()); lo, hi = boot_ci(diff, args.n_boot, rng); pwin = float((diff > 0).mean())
                else:
                    delta = float(ref.cbi.mean() - cur.cbi.mean()); lo, hi = boot_ci_unpaired(ref.cbi.values, cur.cbi.values, args.n_boot, rng)
                    pwin = float((ref.cbi.values[:, None] > cur.cbi.values[None, :]).mean())
            stats_rows.append(dict(species=sp, m=m, n=int(row.n), cbi_mean=row.cbi_mean, cbi_sd=row.cbi_sd, auc_mean=row.auc_mean, auc_sd=row.auc_sd, delta_cbi=delta, ci_lo=lo, ci_hi=hi, p_ref_wins=pwin))
            ci = "—" if np.isnan(delta) else f"{delta:+.3f} [{lo:+.3f}, {hi:+.3f}]"
            pw = "—" if np.isnan(pwin) else f"{pwin:.2f}"
            lines.append(f"| {sp} | {m:.2f} | {int(row.n)} | {row.cbi_mean:.3f} ± {row.cbi_sd:.3f} | {row.auc_mean:.3f} ± {row.auc_sd:.3f} | {ci} | {pw} |")
            tex.append(f"{sp} & {m:.2f} & {row.cbi_mean:.3f} $\\pm$ {row.cbi_sd:.3f} & {row.auc_mean:.3f} $\\pm$ {row.auc_sd:.3f} & {ci.replace('—','--')} & {pw.replace('—','--')} \\\\")
        tex.append("\\midrule")
    text = "\n".join(lines)
    print(text)
    if args.out:
        Path(f"{args.out}_summary.md").write_text(text + "\n")
        pd.DataFrame(stats_rows).to_csv(f"{args.out}_stats.csv", index=False)
        Path(f"{args.out}.tex").write_text("\n".join(tex[:-1]) + "\n")
        print(f"\nwrote {args.out}.csv, {args.out}_stats.csv, {args.out}_summary.md, {args.out}.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
