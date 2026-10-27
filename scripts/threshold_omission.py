#!/usr/bin/env python3
"""Test omission rate of the P10 and maxSSS thresholds (threshold validation).

For every fit of the reference setting (main run set, m = 0.25), the thresholds
are computed on the training data exactly as in scripts/analyze_projections.py
(P10: 10th percentile of the training-presence predictions; maxSSS: maximum of
sensitivity + specificity over training presences and training background) and
applied to the test presences of the other checkerboard colour. The omission
rate is the share of test presences below the threshold; for P10 it is expected
to be close to 10 % if the test presences resemble the training presences.
Writes docs/tables/threshold_omission.csv and prints a summary.

Usage: python scripts/threshold_omission.py [--results runs/revision_main]
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_projections import maxsss_threshold  # noqa: E402

SP = {"Brown_Marmorated_Stink_bug": "BMSB", "Corn_Earworm": "CE", "Spongy_Moth": "SM", "Root_Weevil": "RW", "Spotted_Lanternfly": "SL"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", default=str(ROOT / "runs/revision_main"))
    ap.add_argument("--m", default="0.25")
    args = ap.parse_args()
    rows = []
    for folder, code in SP.items():
        for f in sorted(glob.glob(f"{args.results}/SSP_245/{folder}/{args.m}/lph/2.0/*/experiment_states.pkl")):
            s = joblib.load(f)
            model, xtr, ytr, xte, yte = s["model"], s["x_train"], s["y_train"], s["x_test"], s["y_test"]
            p_tr_pres, p_tr_bg = model.predict(xtr[ytr == 1]), model.predict(xtr[ytr == 0])
            p_te_pres = model.predict(xte[yte == 1])
            t10, tss = float(np.percentile(p_tr_pres, 10)), maxsss_threshold(p_tr_pres, p_tr_bg)
            rows.append(dict(species=code, seed=s.get("seed"), n_test=int(len(p_te_pres)),
                             omission_p10=float((p_te_pres < t10).mean()), omission_maxsss=float((p_te_pres < tss).mean())))
            del s
    d = pd.DataFrame(rows)
    out = ROOT / "docs/tables/threshold_omission.csv"
    d.to_csv(out, index=False)
    g = d.groupby("species")[["omission_p10", "omission_maxsss"]].agg(["mean", "std"]).round(3)
    print(g.reindex(["BMSB", "CE", "SM", "RW", "SL"]).to_string())
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
