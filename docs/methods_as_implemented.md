# Methods as implemented (read from the code, 12 Oct 2026)

This is the ground truth for the Methods section of the paper.
File references are to `MaxEnt_insect_dir/maxent_insect_dir/`.

## Changes in the revision runs (13 Oct 2026)

These apply to every `runs/revision_*` set; the sections below describe the
pipeline as it was for the submitted runs unless they say otherwise.

- **Records outside the established range removed** (`scripts/prepare_inputs.py`):
  spongy moth without the 71 Washington State trap detections (203 -> 132
  records; 66 after 10 km thinning, all with climate data); root weevil with
  records from the states where the EPPO Global Database lists the species as
  present (Florida, Texas, California, Louisiana; 1,107 -> 1,084; 202 after
  thinning; accessed 13 Oct 2026). The 23 removed records are from Alabama (9),
  Georgia (6), South Carolina (4) and Mississippi (4; EPPO: "absent, unreliable
  record"). The first revision runs used Florida, Texas and California only
  (1,046 records); root weevil was rerun on 13 Oct 2026 (`scripts/rerun_species.sh`).
  Complete files: `*_all` keys.
- **All species thinned at 10 km** (`--thin-distance 10000`), the spongy moth
  included.
- **Elevation**: WorldClim 2.1 10 arc-min elevation in metres, masked with the
  baseline land mask (30,097 cells). The submitted runs used an 8-bit
  grayscale rendering of the National Atlas 100 m elevation at ~1 arc-min
  (Spearman rho 0.996 with the WorldClim layer).
- **Correlation filter includes elevation** (`--corr-include-elevation`); being
  first in the scan order it is never dropped. The rule is the upper-triangle
  rule: a column is dropped if |r| > 0.9 with any earlier column in the scan
  order, whether or not that earlier column was itself dropped.
- **Seeds**: repeat k uses `np.random.seed(seed + k)` before the background draw.
- **Projections** on the 10 arc-min climate grid for 2021-2040 and 2041-2060,
  every fit projected onto all four SSPs (ACCESS-CM2) and, for m = 0.25, onto
  four further GCMs (`runs/revision_gcm`).
- **Land mask for comparisons**: the future layers have 221 fewer coastal cells
  than the baseline; areas, centroids and edges are computed on the cells valid
  in both (`analyze_projections.py`), and the maps hide the 221 cells.
- **Class weights**: elapid's `class_weights=100` gives each background point
  100 times the weight of a presence point (maxnet convention), not equal totals.

## Occurrence data

- Files: `config.Insect_list`. CRS EPSG:5070 (NAD83 / Conus Albers, metres).
- Columns show two sources. BMSB (13,755), CE (45,119), SM (203), SL (25,193)
  have EDDMapS fields (`objectid`, `ObsDate`, `DateEnt`, `OccStatus =
  Detected`, `NumCollect`). RW (1,107) has `scientific`, `locality`, `day`
  (GBIF/iNaturalist style). A second BMSB file (`_2007_2023`, 19,474 rows) has
  GBIF `speciesKey = 4485843` but is not the one used.
- Observation dates: BMSB 1999-08 to 2023-04; CE 2007-03 to 2023-06; SM 1991-01
  to 2024-12; RW 2010-05 to 2023-06; SL 2014-06 to 2024-12. All `OccStatus`
  are "Detected"; all records are in the contiguous US (`country = united states`).
- Duplicated coordinates in the raw files: BMSB 632, CE 44,070 (trap sites
  reported repeatedly), SM 4, RW 13, SL 900.
- GBIF backbone keys (api.gbif.org, 12 Oct 2026): *Halyomorpha halys* (Stål,
  1855) 4485843; *Helicoverpa zea* (Boddie, 1850) 1792564; *Lymantria dispar*
  Linnaeus, 1758 1820406 (subspecies *L. d. dispar* 7213579); *Diaprepes
  abbreviatus* (Linnaeus, 1758) 5010133; *Lycorma delicatula* (White, 1845) 5157899.

## Spatial thinning (`utils.spatial_thinning`)

Greedy: points are visited in file order; a point is kept, and every point
within `min_distance` (10,000 m, planar distance in EPSG:5070, cKDTree
`query_ball_point`) of it is marked as considered and skipped. Deterministic for
a given file. `config.spatial_thinning_distance` is 10 km for BMSB, CE, RW, SL
and `None` for SM (reason given in the config: "already well dispersed").

Counts (raw → 10 km thinned → after dropping points on no-data climate cells →
distinct 10-arc-min cells):

| Species | raw | thinned | with climate | distinct cells | one-per-cell of raw |
|---|---|---|---|---|---|
| BMSB | 13,755 | 1,452 | 1,412 | 1,202 | 1,371 |
| CE | 45,119 | 728 | 719 | 687 | 735 |
| RW | 1,107 | 219 | 185 | 150 | 171 |
| SM | 203 | 203 (not thinned) / 95 at 10 km | 193 | 94 | 94 |
| SL | 25,193 | 693 | 664 | 508 | 566 |

A 10-arc-min cell is 18.5 km north–south and 13–17 km east–west over the US,
so 10 km thinning leaves some cells with 2–3 points.

## Predictors

- WorldClim 2.1 bioclimatic variables BIO1–BIO19, 10 arc-min, baseline
  1970–2000, clipped to lon −124.83…−66.83, lat 24.5…49.5 (348 × 150 cells,
  EPSG:4326). Nodata −3.4e38 (baseline) / NaN (future).
- Future: CMIP6 **ACCESS-CM2**, downscaled by WorldClim (`wc2.1_10m_bioc_ACCESS-CM2_ssp{126,245,370,585}_{2021-2040,2041-2060,2061-2080,2081-2100}.tif`), split into per-variable rasters and clipped to the same window.
- Elevation: `Elevation/stanford-zz186ss2071-geotiff.tif`, 8-bit grayscale
  image (values 1–248, grayscale colormap), ~0.0166° (1 arc-min), nodata 0.
  Values are a scaled grayscale rendering of elevation, not metres.
  `run.py` passed its column index as "categorical", but elapid ignores that
  list for DataFrame input and keys on the pandas `category` dtype, so **the
  layer always entered the model as a continuous predictor** (linear, product
  and hinge features; the fitted transformer has `categorical_ = None` and
  424 = 16 × 19 + 120 features for 16 variables). It was excluded from the
  correlation filter in the submitted runs; `--corr-include-elevation` adds it.
- Cropland (USDA CDL most-grown crop) exists in the pipeline (`--use-crop`) but
  was off for every published result.

## Correlation filter (`utils.remove_highly_correlated`)

Pearson correlation on the stacked thinned presences plus background points
(training sample) for BIO1–BIO19 only. Columns are scanned in order BIO1 … BIO19
and a column is dropped if |r| > 0.9 with any earlier retained column, so the
lower-numbered variable of each pair survives. Because the background sample
differs between repeats, the dropped set varies. Over 100 runs per species
(β = 1.5 sweep): BIO10, BIO11, BIO16, BIO17 always dropped; BIO7 dropped in 99 %
(BMSB), 91 % (CE), 100 % (SM, RW), 11 % (SL); BIO6 dropped in 85 % (CE), 100 %
(RW), 60 % (SL); BIO19, BIO13, BIO5, BIO4, BIO9, BIO18, BIO15 dropped in a
minority of runs.

## Background sampling (`utils.spatial_weighted_background`)

1. Kernel density of the thinned presences: quartic (biweight) kernel,
   radius 160 km, output pixel 16 km, EPSG:5070, scaled values
   (`spatial_kde.spatial_kernel_density`, after Silverman 1986). Overlapping
   kernels add. The raster covers the presence bounding box padded by 160 km,
   so it can extend over sea or outside the US.
2. `n_biased = int(m × 10,000)` points are drawn from that raster with
   probability proportional to density (`elapid.sample_bias_file`,
   `np.random.choice` with replacement; a drawn point gets its cell's x/y).
3. `n_uniform = 10,000 − n_biased` points are drawn uniformly from the valid
   cells of the baseline BIO1 raster (`elapid.sample_raster`, with replacement).
4. Points are annotated with the predictors (`elapid.annotate`, `drop_na=True`);
   points on no-data cells (sea, lakes, outside the US window) are dropped.
   Typically 150–850 of the 10,000 are lost (e.g. BMSB 9,820, RW 9,162 kept).
5. No random seed in the submitted runs. The runner now takes `--seed`.

## Train/test split (`utils.get_train_test_split`, `run_utils.prepare_test_train`)

- Presences only: `elapid.checkerboard_split`, square cells of 50 km in
  EPSG:5070, grid origin at the lower-left corner of the presence bounding box,
  alternating colours; "train" is colour 0. Deterministic for a species, so
  every m and every repeat uses the same presence folds. Example BMSB:
  676 train / 734 test presences. The sjoin uses `within`, so the two records
  that define the lower-left corner of the bounding box (x = xmin, y = ymin)
  lie on a grid edge and belong to neither fold (2 records per species unused).
- Training background: the whole sampled background (all ~9,800 points).
- Test background: `Test_data/test.gpkg`, a fixed file of 20,000 uniformly
  sampled points (19,898 with climate data in the revision runs), the same for every run and species.
- Hyper-parameters (m, feature classes, β) were compared on this same test
  fold; there was no separate selection fold. `--swap-folds` exchanges the
  colours for a two-fold check.

## Model (`run_utils.train_model`, elapid 1.0.2)

`elapid.MaxentModel(transform="cloglog", tau=τ, beta_multiplier=β,
feature_types=...)`, fitted with scikit-learn `LogisticRegression(penalty="l1",
solver="liblinear", C = f(β))`, `class_weights=100`, 10 hinge knots per
variable, clamping on. τ = 0.5 (BMSB, CE, SL) and 0.1 (RW, SM); τ only affects
the logistic transform, cloglog output is 1 − exp(−exp(η) · exp(H)).
Feature strings: l, lq, lqh, lph, lqhp, lqhpt; the paper's default is lph.

## Evaluation (`run_utils.evaluate`)

- AUC: `roc_auc_score` of test presences vs test background.
- CBI (`Continuous_boyce_index.continuous_boyce_index`): predictions at test
  presences (P) and test background (E); 20 equal-width bins between the min and
  max of the background predictions; F = (share of P in bin)/(share of E in
  bin); bins with no background are dropped; CBI = Spearman correlation between
  F and bin midpoints. Reported as `cbi_test["Spearman.cor"]`.
- Permutation importance: `sklearn.inspection.permutation_importance` on the
  test fold, 10 permutations, `random_state=42`, ROC-AUC scorer on
  `predict_proba`.

## Projections and coverage

`elapid.apply_model_to_rasters` on the clipped baseline and future stacks
(same columns as training). Until 12 Oct 2026 the first raster of the stack,
the 1 arc-min elevation layer, was the template grid, so the submitted maps
and coverage shares were computed on a 4096 x 1886 grid with the climate
layers resampled up. The revision runs use the first bioclim layer as the
template (348 x 150 cells) and average the elevation layer into each cell. The coverage tables counted cells with cloglog
output > 0.5 as suitable and reported the share of valid cells; the change is
`(future − current)/current`. In the submitted runs each SSP table came from a
separate set of 20 fits (so the "current" row differs between SSP tables); the
runner now has `--project-pathways` to project one fit onto all four SSPs.

## Accessible areas (Revision 2)

`--accessible-area <def>` reads `data/data/accessible_area/<Species>_<def>.tif`
(climate grid, 1 = inside; `scripts/accessible_area.py`). The kernel surface is
built from all thinned records as before, then set to nodata outside M; the
uniform background is drawn from a copy of the Bio1 raster masked to M; thinned
records outside M (only records on cells without climate data) are dropped; the
fixed test background is limited to the points inside M. Without the option the
runner is unchanged (root weevil, seed 1000: identical CBI, AUC and background).
