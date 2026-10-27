# Reproducibility report (12 Oct 2026)

Question: can the results of the submitted *Insects* manuscript be reproduced on
this machine, without access to Zeus?

## Short answer

- **Table 2 (CBI and AUC versus m): yes.** A full local rerun (29 Sep 2026,
  `runs/paper_m_table`, lph, β = 2.0, 20 repeats, 10,000 background points)
  reproduces every cell within one standard deviation. See the table below.
- **Figures 4–5, 6–10 (maps): yes in substance.** `runs/m_sweep` (26 Sep 2026,
  lph, β = 1.5, same m values, 20 repeats) contains the current and future
  rasters for SSP2–4.5; the maps can be redrawn with
  `MaxEnt_insect_dir/notebooks/paper_visualization.ipynb`.
- **Tables 3–7 (best configurations, coverage change): not from the original
  states.** They were computed on Zeus from `experiment_states.pkl` files that
  were never copied; only three summary CSVs (`data/experiment_summary/`, BMSB,
  RW, SM, 4 runs per cell) came across. Table 3 omits CE and SL because those
  two summaries were never produced. The coverage numbers in Tables 4–7 (20
  repeats) are not in the CSVs either. They can be re-derived from local runs,
  which is what the revision does.
- **Table 9 and Section 3.3 (feature importance): not reproduced.** Local runs
  (both β = 1.5 and 2.0) rank BIO2, BIO1, BIO5, BIO15, BIO4 at the top and
  elevation 5th–10th (mean 7.5; never first). The submitted Table 9 shows elevation first in 20/20 runs
  for β ≥ 1.0. Which Zeus runs produced that table is not recorded.
- **Figure 11 (drift experiment): code missing.** `feature_important_drift.py`
  and `feature_importance_drift.ipynb` were gitignored and are not in the
  backup zip or the Zeus text copy. The experiment is re-implemented in
  `scripts/drift_experiment.py` for the revision.

## Table 2: submitted vs local rerun (CBI, mean ± SD over 20 repeats)

| Species | m | Submitted | Local rerun (Sep 2026) |
|---|---|---|---|
| BMSB | 0 / 0.25 / 0.5 / 0.75 / 1 | 0.980 / **0.984** / 0.973 / 0.976 / 0.845 | 0.984 / 0.984 / 0.976 / 0.976 / 0.855 |
| CE | | 0.957 / 0.967 / **0.978** / 0.976 / 0.401 | 0.952 / 0.965 / 0.973 / 0.977 / 0.437 |
| SM | | 0.250 / **0.695** / 0.550 / 0.489 / 0.331 | 0.245 / 0.701 / 0.590 / 0.485 / 0.355 |
| RW | | 0.855 / **0.926** / 0.924 / 0.923 / 0.518 | 0.855 / 0.924 / 0.937 / 0.940 / 0.524 |
| SL | | 0.948 / **0.976** / 0.969 / 0.847 / 0.469 | 0.953 / 0.975 / 0.896 / 0.827 / 0.477 |

AUC agrees to two or three decimals in every cell. Note that in the rerun the
root weevil peaks at m = 0.75, not 0.25: the differences between m = 0.25, 0.5
and 0.75 for RW (and BMSB) are inside the sampling noise.

Command used: `bash scripts/rerun_paper_m_table.sh` then
`python scripts/summarize_m_table.py` (reads `auc["AUC_test"]` and
`cbi_test["Spearman.cor"]` from each `experiment_states.pkl`).

## What the code and data say that the manuscript does not

These were found while checking reproducibility and drive the revision.

| Topic | Manuscript | Actual |
|---|---|---|
| Future climate | "WorldClim … four SSPs" | One GCM, **ACCESS-CM2** (file names in `data/data/SSP_*`; SSP2–4.5 Bio1 is byte-identical to the WorldClim download). No ensemble. |
| "Current (2020)" | 2020 | Baseline 1970–2000; "2040" = 2021–2040, "2060" = 2041–2060 |
| Buffer | "buffer around presences" (no radius) | Quartic kernel density, 160 km radius, 16 km grid, EPSG:5070; sampled with replacement, unseeded |
| Thinning | 10 km "roughly matching" 10 arc-min; SM 203 → 193 | Greedy cKDTree 10 km in EPSG:5070 (equal-area). SM was **not** thinned; 203 → 193 is the no-data drop. After thinning, 210/1412 BMSB and 156/664 SL points still share a 10-arc-min cell |
| Checkerboard | no size | 50 km cells, origin at presence bounding box, applied to presences only; test background is a fixed uniform 20,000-point file |
| CBI | "continuous Boyce index" | Own implementation of Hirzel et al. 2006 eq. 4: 20 equal-width bins over the range of background predictions, Spearman of P/E vs bin midpoints, NaN bins dropped |
| Correlation filter | "pairs with r ≥ 0.9 removed" | Pearson > 0.9 on stacked presence + background; keeps the lower-numbered Bio variable; elevation excluded; dropped set varies by repeat (usually BIO10, BIO11, BIO16, BIO17, often BIO7/BIO6) |
| Elevation | "elevation profile" | 8-bit grayscale elevation image (Stanford `zz186ss2071`, ~1 arc-min), values 1–248, used as a continuous predictor (the code's "categorical" index is ignored by elapid for DataFrames) |
| Occurrence data | "GBIF" | BMSB, CE, SM, SL files carry EDDMapS fields (`ObsDate`, `OccStatus`, `NumCollect`); RW file carries GBIF-style fields. Dates: BMSB 1999–2023, CE 2007–2023, SM 1991–2024, RW 2010–2023, SL 2014–2024 |
| Permutation importance | "permutation importance" | sklearn `permutation_importance`, 10 permutations, ROC-AUC, computed on the test fold |
| Seeds | "different random seeds" | No seeds were set; every repeat is a fresh unseeded draw |

## Inputs present locally

`data/data/Species_Data/Clean_Data/` (five species), `Test_data/test.gpkg`,
`US_shapefile/`, `Elevation/`, `Bioclim_worldclim_average_1970_2000/wc2.1_10m_bio/Clipped/In_tiff_format/`,
`SSP_{126,245,370,585}/Bioclim_worldclim_average_{2021_2040,2041_2060,2061_2080,2081_2100}/Clipped/In_tiff_format/`.
Cropland (`crop_data/`, 65 GB) is present but not used by any published table.

## Note on the revision runs

The revision runs (`runs/revision_*`, see `docs/run_index.md`) are not a
reproduction of the submitted runs: they use seeds, thin all species at 10 km,
drop the out-of-range spongy moth and root weevil records, use the WorldClim
elevation layer, include elevation in the correlation filter, and project one
fit onto every scenario. Their numbers therefore differ from the submitted
tables by design. The reproduction of the submitted performance table above
(unseeded, original inputs) is given as Table R1 in the response letter (it was Supplementary Table S1 in an earlier draft of the revision).
