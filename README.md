# maxent-insect-sdm

MaxEnt species distribution models for five pest insects of US agriculture and
forestry, fitted on the contiguous United States and projected onto CMIP6
climate scenarios. This repository holds the Python package, the run scripts,
the documentation of every modelling choice, and the processed data released with the paper.
The manuscript source is not part of this public branch.

Paper: Chouhan, Zavala-Romero & Haseeb, *Evaluating MaxEnt modeling strategies
for predicting climatically suitable areas of pest insects under climate change
scenarios* (under revision at *MDPI Insects*; preprint
[bioRxiv 10.64898/2026.04.18.719331](https://doi.org/10.64898/2026.04.18.719331)).
Funding: USDA NIFA, Florida A&M University, Accession 1028629.

Species: brown marmorated stink bug *Halyomorpha halys*, corn earworm
*Helicoverpa zea* (native to North America), spongy moth *Lymantria dispar*,
Diaprepes root weevil *Diaprepes abbreviatus*, spotted lanternfly *Lycorma delicatula*.

## Layout

```text
MaxEnt/
├── MaxEnt_insect_dir/      # the model package: python -m maxent_insect_dir.run
├── data/data/              # occurrences, WorldClim 2.1, elevation, US boundary (not in git)
├── runs/                   # model outputs, one folder per run set (not in git)
├── scripts/                # environment, reruns, revision analyses
├── docs/                   # reproducibility report, methods as implemented, run index, result tables
├── data_release/           # processed occurrence records and the fixed test background
├── tools/maxent.jar        # Java MaxEnt, reference only; the runner uses elapid
```

## Environment

```bash
bash scripts/setup_venv.sh                      # .venv; installs ../elapid/elapid and this package
export MAXENT_DATA_ROOT=/home/pankaj/Postdoc/MaxEnt/data
export MAXENT_RESULTS_ROOT=/home/pankaj/Postdoc/MaxEnt/runs/my_run
export MPLBACKEND=Agg
.venv/bin/python -m maxent_insect_dir.run --help
```

elapid 1.0.2 is installed from the sibling checkout `../elapid/elapid`.

## Reproduce the published performance table

CBI and AUC versus the mixing coefficient *m* (Table 2 of the submitted paper):
features `lph`, β = 2.0, *m* ∈ {0, 0.25, 0.5, 0.75, 1}, 20 repeats, 10,000
background points, elevation on, cropland off.

```bash
bash scripts/rerun_paper_m_table.sh        # five species in parallel, ~75 min
.venv/bin/python scripts/summarize_m_table.py
```

The local rerun of 29 Sep 2026 reproduces every cell of Table 2 within one
standard deviation; see [docs/reproducibility_report.md](docs/reproducibility_report.md).

## Runner options

`python -m maxent_insect_dir.run --pathways SSP_245 [options]`

| Option | Meaning |
|---|---|
| `--insects`, `--feature-types`, `--beta-multipliers`, `--bias-mix`, `--repeats` | the experiment grid |
| `--background-count` | background points (10,000) |
| `--seed N` | repeat *k* uses seed N + k (background draws become repeatable) |
| `--kernel-radius M` | radius of the presence kernel used for the biased background (160,000 m) |
| `--thin-distance M` | thinning distance for every species (overrides `config.py`) |
| `--swap-folds` | exchange the checkerboard colours |
| `--corr-include-elevation` | add elevation to the correlation filter |
| `--project-pathways SSP_126 SSP_245 SSP_370 SSP_585` | project each fitted model onto every pathway |
| `--skip-projections` | metrics only |

Outputs: `$MAXENT_RESULTS_ROOT/<SSP>/<insect>/<m>/<feature>/<beta>/<run>/` with
`experiment_states.pkl` (joblib; metrics, model, data), diagnostic PNGs and
suitability GeoTIFFs.

## Data

Raw inputs are not in this repository. Occurrence files go under
`data/data/Species_Data/Clean_Data/`; climate under
`data/data/Bioclim_worldclim_average_1970_2000/` and `data/data/SSP_*/`
(WorldClim 2.1, CMIP6 ACCESS-CM2); extra GCMs for the revision under
`data/data/GCM_ensemble/` (`scripts/download_gcm_ensemble.sh`).

What the code actually does with these inputs (kernel radius, thinning,
checkerboard, CBI bins, elevation encoding, correlation rule) is written down in
[docs/methods_as_implemented.md](docs/methods_as_implemented.md).

## Revision (Oct 2026)

The revised analyses (seeded runs, five climate models, thresholds, shift metrics,
accessible areas) and the exact commands of every run set are in
[docs/run_index.md](docs/run_index.md). Processed occurrence records with their
checkerboard fold and the fixed test background are in `data_release/`.

Pipeline of the revision (all under `scripts/`):

| Step | Script | Output |
|---|---|---|
| derived inputs (filtered occurrence files, WorldClim elevation) | `prepare_inputs.py` | `data/data/...` |
| run sets (main, swap, radius, grid, sm_unthinned, allrecords) | `launch_revision_runs.sh <set>` | `runs/revision_*` |
| accessible areas M per species (Revision 2) | `accessible_area.py` | `data/data/accessible_area/*.tif` |
| background experiment inside M (Revision 2) | `launch_revision2_M.sh` | `runs/revision2_M_*` |
| tables and maps for the M analysis | `accessible_area_tables.py` | `docs/tables/accessible_area_results.csv`, paper `tables/accessible_*.tex` |
| rerun one species after its input file changed (all sets, split per m / feature string) | `rerun_species.sh <Species>` | `runs/revision_*` |
| drift experiment | `drift_experiment.py` | `runs/revision_drift/` |
| extra GCM layers | `download_gcm_ensemble.sh`, `prepare_gcm_layers.py` | `data/data/GCM_ensemble/` |
| GCM projections of the fitted models | `project_gcm_ensemble.py --species <sp>` | `runs/revision_gcm/` |
| areas, thresholds, centroid/edge shifts, GCM spread | `analyze_projections.py --gcm-root runs/revision_gcm --out docs/tables/projections` | `docs/tables/projections_*.csv` |
| Table 2 with bootstrap CIs; importance stability | `table2_stats.py`, `importance_table.py` | `docs/tables/` |
| paper table bodies and figures | `make_paper_tables.py`, `make_paper_figures.py all` | table bodies and figures in the folder given by `MAXENT_PAPER_DIR` |
| facts for the text | `summarize_for_text.py` | printed |
| record checks (dates, state centroids, coordinate precision) | `record_checks.py` | `docs/tables/record_checks.txt` |
| threshold check (test omission rate at P10 and maxSSS) | `threshold_omission.py` | `docs/tables/threshold_omission.csv` |
| processed occurrence tables | `export_processed_data.py` | `data_release/` |

`data_release/` holds the thinned occurrence records with their checkerboard
fold and the fixed 20,000-point test background (CSV).
