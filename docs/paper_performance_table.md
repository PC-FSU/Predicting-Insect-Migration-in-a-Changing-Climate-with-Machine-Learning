# Performance table (CBI and AUC versus m)

The table in the manuscript (`table:performance-metrics`) is the mean and
sample standard deviation of test CBI and test AUC over 20 stochastic repeats.
Each row is one mixing coefficient `m`.

## Where the published numbers were read from

They were not recomputed for the comparison against the manuscript. They were
read from the states already stored on Zeus:

```text
/data/Maxent/data/results/SSP_245/<species>/<m>/<run>/experiment_states.pkl
```

`<species>` is `Brown_Marmorated_Stink_bug`, `Corn_Earworm`, `Root_Weevil`,
`Spongy_Moth`, or `Spooted_Lanternfly` (the folder name keeps that spelling).
`<m>` is `0`, `0.25`, `0.5`, `0.75`, or `1.0`. Each of those directories holds
20 run folders dated 18–19 May 2025, sitting directly under `<m>/`, not under
a feature/beta subdirectory. The June 2025 feature-by-beta grid is a different
experiment and lives one level deeper (`<m>/<feature>/<beta>/`).

Each state is a joblib dump. The table cells are:

- `auc["AUC_test"]`
- `cbi_test["Spearman.cor"]`

Every one of those 500 models stored `feature_types = [linear, hinge, product]`
and `beta_multiplier = 2.0`. The stink-bug state that was opened also stored
`tau = 0.5`, `use_elevation = True`, `use_crop = False`,
`background_count = 10000`, training climate `1970_2000` / `WorldClim`.

## What a local rerun uses

`scripts/rerun_paper_m_table.sh` asks the current package for the same slice:

| setting | value |
|---|---|
| feature string | `lph` (linear, product, hinge) |
| beta multiplier | 2.0 |
| m | 0, 0.25, 0.5, 0.75, 1 |
| repeats | 20 |
| background points | 10000 |
| elevation | on |
| cropland | off |
| tau | `config.tau` (0.5; root weevil and spongy moth 0.1) |
| projections | skipped |

Outputs land in `runs/paper_m_table/`. Background sampling has no seed, so a
new run will not reprint the May digits. `scripts/summarize_m_table.py` prints
the same mean ± std layout as the manuscript table.

## Inputs that must be present

All of these are already under `data/data/`:

- `Species_Data/Clean_Data/` for the five species
- `Test_data/test.gpkg`
- `US_shapefile/US_shapefile.shp`
- `Elevation/stanford-zz186ss2071-geotiff.tif`
- `Bioclim_worldclim_average_1970_2000/wc2.1_10m_bio/Clipped/In_tiff_format/Bio1.tif` through `Bio19.tif`

The runner also resolves the four SSP2–4.5 future periods. Those tifs are on
disk too. They are not sampled when `--skip-projections` is set. Cropland is
not read for this table.
