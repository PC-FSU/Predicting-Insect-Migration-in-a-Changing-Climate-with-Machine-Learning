#!/usr/bin/env python3
"""Mean and sample std of test AUC and test CBI for the local performance-table rerun.

Reads experiment_states.pkl under $MAXENT_RESULTS_ROOT (default runs/paper_m_table).
Only folders whose names contain feature lph and beta 2.0 are included, so an
older beta-1.5 sweep in the same tree is left out.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(os.environ.get("MAXENT_RESULTS_ROOT", ROOT / "runs" / "paper_m_table"))
SPECIES = [
    "Brown_Marmorated_Stink_bug",
    "Corn_Earworm",
    "Spongy_Moth",
    "Root_Weevil",
    "Spotted_Lanternfly",
    "Spooted_Lanternfly",
]


def metric_files(species: str, mix: str) -> list[Path]:
    """Return state files for one species and one mixing value."""
    base = RESULTS / "SSP_245" / species / mix / "lph" / "2.0"
    if not base.is_dir():
        return []
    return sorted(base.glob("*/experiment_states.pkl"))


def summarize(paths: list[Path]) -> tuple[int, float, float, float, float]:
    """Load AUC and CBI from each state and return count, means, and sample stds."""
    aucs: list[float] = []
    cbis: list[float] = []
    for path in paths:
        state = joblib.load(path)
        aucs.append(float(state["auc"]["AUC_test"]))
        cbis.append(float(state["cbi_test"]["Spearman.cor"]))
        del state
    auc = np.asarray(aucs, dtype=float)
    cbi = np.asarray(cbis, dtype=float)
    return (
        int(auc.size),
        float(auc.mean()),
        float(auc.std(ddof=1)),
        float(cbi.mean()),
        float(cbi.std(ddof=1)),
    )


def main() -> int:
    print(f"results {RESULTS}")
    print(f"{'species':32} {'m':6} {'n':4} {'CBI':16} {'AUC':16}")
    found = 0
    for species in SPECIES:
        for mix in ("0", "0.25", "0.5", "0.75", "1.0"):
            paths = metric_files(species, mix)
            if not paths and mix == "0.5":
                paths = metric_files(species, "0.50")
            if not paths and mix == "1.0":
                paths = metric_files(species, "1")
            if not paths and mix == "0":
                paths = metric_files(species, "0.0")
            if not paths:
                continue
            n, auc_mean, auc_std, cbi_mean, cbi_std = summarize(paths)
            found += n
            print(
                f"{species:32} {mix:6} {n:4d} "
                f"{cbi_mean:.3f} ± {cbi_std:.3f}  "
                f"{auc_mean:.3f} ± {auc_std:.3f}"
            )
    if found == 0:
        print("no lph / beta 2.0 states found", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
