#!/usr/bin/env python3
"""Permutation-importance stability across repeats (replacement for Table 9).

For one species, feature string, beta and m, reads the permutation importance
stored in every experiment_states.pkl and reports, per predictor: mean ± SD
importance, how often it ranked in the top 3 and top 5, and its mean rank.
Writes markdown and LaTeX. With --all-species, one block per species.

Usage:
    python scripts/importance_table.py --results runs/revision_main --beta 2.0 --m 0.25 \
        --species Brown_Marmorated_Stink_bug --out docs/tables/importance_bmsb
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

SHORT = {
    "Brown_Marmorated_Stink_bug": "BMSB",
    "Corn_Earworm": "CE",
    "Spongy_Moth": "SM",
    "Root_Weevil": "RW",
    "Spotted_Lanternfly": "SL",
}
NAMES = {
    "Bio1": "annual mean temperature", "Bio2": "mean diurnal range", "Bio3": "isothermality",
    "Bio4": "temperature seasonality", "Bio5": "max temp. warmest month", "Bio6": "min temp. coldest month",
    "Bio7": "temperature annual range", "Bio8": "mean temp. wettest quarter", "Bio9": "mean temp. driest quarter",
    "Bio10": "mean temp. warmest quarter", "Bio11": "mean temp. coldest quarter", "Bio12": "annual precipitation",
    "Bio13": "precip. wettest month", "Bio14": "precip. driest month", "Bio15": "precip. seasonality",
    "Bio16": "precip. wettest quarter", "Bio17": "precip. driest quarter", "Bio18": "precip. warmest quarter",
    "Bio19": "precip. coldest quarter", "elevation": "elevation",
}


def collect(results: Path, pathway: str, species: str, m: str, feature: str, beta: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Importance per fit (NaN for predictors removed by the correlation filter) and a kept table."""
    rows, kept_rows = [], []
    for mm in {m, m.rstrip("0").rstrip(".") if "." in m else m, f"{float(m):.2f}", f"{float(m):g}"}:
        for path in sorted(glob.glob(str(results / pathway / species / mm / feature / beta / "*" / "experiment_states.pkl"))):
            s = joblib.load(path)
            fi = s["feature_importance"].astype(float)
            fi.name = path
            rows.append(fi)
            kept_rows.append(pd.Series({c: True for c in s["cols_to_keep"] if c != "geometry"}, name=path))
            del s
    if not rows:
        raise SystemExit(f"no states for {species} m={m} under {results}")
    imp = pd.DataFrame(rows)
    kept = pd.DataFrame(kept_rows).reindex(columns=imp.columns).fillna(False).astype(bool)
    return imp, kept


def summarise(imp: pd.DataFrame, kept: pd.DataFrame) -> pd.DataFrame:
    """Predictors removed by the correlation filter get importance 0 in that fit (they tie last)."""
    filled = imp.fillna(0.0)
    # predictors removed by the correlation filter (NaN) rank after every kept predictor
    ranks = imp.rank(axis=1, ascending=False, method="min", na_option="bottom")
    out = pd.DataFrame(
        {
            "mean": filled.mean(),
            "sd": filled.std(ddof=1),
            "top3": (ranks <= 3).sum(),
            "top5": (ranks <= 5).sum(),
            "mean_rank": ranks.mean(),
            "n_present": kept.sum(),                 # fits in which the predictor passed the correlation filter
            "n_zero": ((filled == 0) & kept).sum(),  # kept, but every coefficient shrunk to zero
        }
    )
    return out.sort_values("mean", ascending=False)


def render(name: str, summ: pd.DataFrame, n_runs: int) -> tuple[str, str]:
    md = [f"### {name} ({n_runs} runs)", "", "| predictor | mean ± SD | top-3 | top-5 | mean rank | kept in | zero in |", "|---|---|---|---|---|---|---|"]
    tex = []
    for var, r in summ.iterrows():
        label = f"{var} ({NAMES.get(var, '')})" if var != "elevation" else "elevation"
        md.append(f"| {label} | {r['mean']:.3f} ± {r['sd']:.3f} | {int(r.top3)} | {int(r.top5)} | {r.mean_rank:.1f} | {int(r.n_present)} | {int(r.n_zero)} |")
        kept_txt = f"{int(r.n_present)}" + (f" ({int(r.n_zero)} zero)" if r.n_zero else "")
        tex.append(f"{var} & {NAMES.get(var, '')} & {r['mean']:.3f} $\\pm$ {r['sd']:.3f} & {int(r.top3)} & {int(r.top5)} & {r.mean_rank:.1f} & {kept_txt} \\\\")
    return "\n".join(md) + "\n", "\n".join(tex) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default="runs/paper_m_table")
    ap.add_argument("--pathway", default="SSP_245")
    ap.add_argument("--species", default="Brown_Marmorated_Stink_bug")
    ap.add_argument("--all-species", action="store_true")
    ap.add_argument("--feature", default="lph")
    ap.add_argument("--beta", default="2.0")
    ap.add_argument("--m", default="0.25")
    ap.add_argument("--out", default=None)
    ap.add_argument("--top", type=int, default=None, help="only the TOP predictors by mean score in the LaTeX/markdown output")
    args = ap.parse_args()

    species_list = list(SHORT) if args.all_species else [args.species]
    md_all, tex_all = [], []
    for sp in species_list:
        imp, kept = collect(Path(args.results), args.pathway, sp, args.m, args.feature, args.beta)
        summ = summarise(imp, kept)
        if args.top:
            summ = summ.head(args.top)
        md, tex = render(f"{SHORT[sp]} — {args.feature}, beta {args.beta}, m {args.m}", summ, len(imp))
        print(md)
        md_all.append(md)
        header = f"\\multicolumn{{7}}{{l}}{{\\textbf{{{SHORT[sp]}}} ({len(imp)} fits)}} \\\\\n" if args.all_species else ""
        tex_all.append(f"% {sp}\n" + header + tex + ("\\midrule\n" if args.all_species else ""))
        if args.out:
            imp.to_csv(f"{args.out}_{SHORT[sp]}_raw.csv")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(f"{args.out}.md").write_text("\n".join(md_all))
        Path(f"{args.out}.tex").write_text("\n".join(tex_all))
        print(f"wrote {args.out}.md / .tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
