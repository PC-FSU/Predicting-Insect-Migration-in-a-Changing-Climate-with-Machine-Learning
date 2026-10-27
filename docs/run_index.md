# Run index

Every model run set on this machine, with the exact command. All sets write
under `runs/<name>/` (not in git). States are `experiment_states.pkl` (joblib);
since 12 Oct 2026 they record `git_commit`, `argv`, `seed` and `repeat_index`.

| Set | Date | Purpose | Design | Command |
|---|---|---|---|---|
| `runs/m_sweep` | 26 Sep 2026 | local rerun of the projection sweep | lph, β 1.5, m ∈ {0,…,1}, 20 repeats, unseeded, SM unthinned, projections for SSP_245 | `python -m maxent_insect_dir.run --pathways SSP_245 --bias-mix 0 0.25 0.5 0.75 1 --repeats 20` |
| `runs/paper_m_table` | 29 Sep 2026 | reproduce Table 2 | lph, β 2.0, same m, 20 repeats, unseeded, SM unthinned, metrics only | `bash scripts/rerun_paper_m_table.sh` |
| `runs/elev_ab` | 12 Oct 2026 | elevation "categorical" vs continuous | BMSB, RW, SM; m 0.25; 5 seeded repeats (seed 100–104) each way | see `docs/revision_plan.md`; result: identical, the flag was a no-op |
| `runs/revision_main` | 13 Oct 2026 (restarted 00:08) | reference set of the revision | lph, β 2.0, m ∈ {0, 0.25, 0.5, 0.75, 1}, 20 repeats, seeds 1000–1019, all species thinned at 10 km, elevation (WorldClim 2.1, metres, 10 arc-min) in the correlation filter, spongy moth without the Washington detections (132 records), root weevil from the EPPO-present states FL/TX/CA/LA (1,084; rerun 13 Oct 16:05), one fit projected onto SSP1-2.6 / 2-4.5 / 3-7.0 / 5-8.5 for 2021–2040 and 2041–2060 on the climate grid (348 × 150) | `bash scripts/launch_revision_runs.sh main` |
| `runs/revision_swap` | 13 Oct 2026 (restarted 00:08) | two-fold check | as main, checkerboard colours exchanged, metrics only | `bash scripts/launch_revision_runs.sh swap` |
| `runs/revision_radius80`, `runs/revision_radius320` | 13 Oct 2026 (done) | kernel-radius × m sensitivity | lph, β 2.0, m ∈ {0.25, 0.5, 0.75}, 10 repeats, radius 80 km / 320 km | `bash scripts/launch_revision_runs.sh radius` |
| `runs/revision_grid` | 13 Oct 2026 (done) | feature class × β selection on the baseline | 6 feature strings × 5 β at m 0.25, 4 repeats (seeds 2000–2003), projections to all SSPs | `bash scripts/launch_revision_runs.sh grid` |
| `runs/revision_drift` | 12 Oct 2026 (done) | replicated background-drift experiment | BMSB, bioclim only, lph/2.0, m 0.25, seed 5000; drift 1/5/10/50 km × 10 replicates + 10 fresh redraws; predictor set fixed to the base fit | `python scripts/drift_experiment.py --species Brown_Marmorated_Stink_bug --m 0.25 --beta 2.0 --replicates 10 --out runs/revision_drift` |
| `runs/revision_gcm` | 13 Oct 2026 (done; root weevil redone after its rerun) | projections of the 20 m=0.25 main-set models per species onto 4 extra GCMs | MPI-ESM1-2-HR, MIROC6, UKESM1-0-LL, EC-Earth3-Veg × 4 SSPs × 2 periods; ACCESS-CM2 comes from the main set's own rasters | `python scripts/project_gcm_ensemble.py --species <sp>` (one process per species) |
| `runs/revision_sm_unthinned` | 13 Oct 2026 (done) | spongy moth, all 203 records and no thinning (as submitted), otherwise as main, metrics only | 5 m × 20 repeats | `bash scripts/launch_revision_runs.sh sm_unthinned` |
| `runs/revision_allrecords` | 13 Oct 2026 (done) | spongy moth and root weevil with all records (incl. out-of-range), thinned, SSP2-4.5 projections | 2 species × 5 m × 20 repeats | `bash scripts/launch_revision_runs.sh allrecords` |
| `runs/revision_percell` | 13 Oct 2026 (done) | one record per 10 arc-min cell after 10 km thinning | BMSB, RW, SL; lph, β 2.0, m 0.25, 20 repeats, seeds 1000–1019, SSP2-4.5 projections | `bash scripts/launch_revision_runs.sh percell` |
| `runs/revision_rw_fltxca` | 13 Oct 2026 (done, 16:43) | root weevil sensitivity: first revision filter (Florida, Texas, California only; 1,046 records) | `Root_Weevil_FL_TX_CA`, lph, β 2.0, m ∈ {0, …, 1}, 20 repeats, seeds 1000–1019; SSP2-4.5 projections at m 0.25 only (Table S6) | five processes, one per m: `python -m maxent_insect_dir.run --insects Root_Weevil_FL_TX_CA --pathways SSP_245 --background-count 10000 --thin-distance 10000 --corr-include-elevation --feature-types lph --beta-multipliers 2.0 --bias-mix <m> --repeats 20 --seed 1000 [--skip-projections unless m = 0.25]` |
| `runs/revision2_M_eco`, `runs/revision2_M_eco100`, `runs/revision2_M_rec200` | 13 Oct 2026 (Revision 2) | background experiment inside species-specific accessible areas M (accessible area) | lph, β 2.0, m ∈ {0, …, 1}, 20 repeats, seeds 1000–1019, 10 km thinning, elevation in the filter; background and test background limited to `data/data/accessible_area/<Species>_<def>.tif`; SSP2-4.5 projection | `bash scripts/launch_revision2_M.sh` |

Seeds: `np.random.seed(seed + repeat_index)` is set once per experiment before
the background draw, so repeat *k* of every m and every species starts from the
same random state (partially paired draws across m).

Analysis outputs (tables, CSVs) go to `docs/tables/` and are committed.

Projection grid: until 12 Oct 2026 `elapid.apply_model_to_rasters` used the
first raster of the stack (the 1 arc-min elevation layer) as its template, so
every projection had 4096 × 1886 cells and took minutes. `run_utils.compute_projections`
now uses the first bioclim layer as template (348 × 150 cells); elevation is
averaged into each climate cell. `runs/m_sweep` rasters are on the old grid.

Drift result (BMSB, m 0.25, lph/2.0, bioclim only, 10 replicates per level):
share of points changing cell 1 / 5 / 18 / 83 % at 1 / 5 / 10 / 50 km; Spearman ρ with
the base importance vector 0.992 / 0.990 / 0.985 / 0.953; fresh background draws
0.914 ± 0.047. Displacement changes the ranking less than a new draw does.

GCM ensemble layers: `data/data/GCM_ensemble/<GCM>/ssp<N>/<period>/Clipped/In_tiff_format/`
(32 files clipped and masked like the ACCESS-CM2 layers, self-test identical).
Projection timing: 0.2 s per raster on the climate grid; the on-the-fly
resampling of the 1 arc-min elevation layer is not a bottleneck
(`data/data/Elevation/elevation_10m_avg.tif` is a pre-averaged copy, unused).

Restart on 13 Oct 2026 00:08 (after the internal reviews): the first main/swap
launches of 12 Oct (old 8-bit elevation layer, all spongy-moth and root-weevil
records) were stopped at ~40 % / ~60 % and deleted. Changes: elevation =
`data/data/Elevation/wc2.1_10m_elev_clipped.tif` (WorldClim 2.1, metres, clipped
and masked like the climate layers; `MAXENT_ELEVATION=legacy` restores the old
layer, which has Spearman rho 0.996 with it); `config.Insect_list` now points
`Spongy_Moth` to `spongy_moth_est_noWA.gpkg` (Washington State trap detections
of eradicated introductions removed: 203 -> 132 records, 66 after 10 km
thinning) and `Root_Weevil` to `Root_Weevil_est_FL_TX_CA.gpkg` (1,107 -> 1,046;
193 after thinning); the complete files are the `*_all` keys.
Software: Python 3.13.11, elapid 1.0.2 (local checkout; identical to the PyPI
wheel except an added `evaluate.py` module and its import, not used here),
scikit-learn 1.5.2, numpy 1.26.4, scipy 1.17.1, pandas 3.0.6, rasterio 1.4.4,
geopandas 1.1.4, shapely 2.1.2.

Second relaunch on 13 Oct 2026 at about 13:08: the 00:08 sets (elevation masked with the
future-layer land mask, which removed 21 root-weevil, 36 stink-bug, 22
lanternfly and 7 corn-earworm records on coastal cells) were deleted. All sets
were relaunched with the elevation masked by the baseline land mask
(`scripts/prepare_inputs.py`) and areas compared on the common cells:
main, swap, grid (two feature groups per species), allrecords and
sm_unthinned at about 13:08 (grid paused at 13:15 and resumed when main finishes, to avoid oversubscribing the 16 cores); radius and the extra-GCM projections start
automatically when swap and main finish. The drift set (bioclimatic
predictors only) is unaffected and was kept.

Root-weevil rerun on 13 Oct 2026 at about 16:05: the root-weevil filter was changed
from Florida/Texas/California to the states where the EPPO Global Database lists
the species as present (adds Louisiana, 38 records; removes AL 9, GA 6, SC 4, MS 4;
1,084 records, 202 after 10 km thinning). `bash scripts/rerun_species.sh Root_Weevil`
deleted the root-weevil results of main, swap, radius80/320, grid, percell and gcm
and relaunched them split by m, radius x m and feature string (23 processes, same
seeds, so the split gives the same fits as one combined launch). The extra-GCM
projections were redone afterwards. `Root_Weevil_all` (allrecords) did not change.

Provenance. Each state records `git_commit` = the repository HEAD when the fit was
SAVED, not when its process loaded the code, so fits saved after a commit show the
newer hash although the process ran the older code. What each set actually ran:
- main, swap, grid, allrecords, sm_unthinned (launched 13:08): the package as in
  commit 4710751 ("Revision after internal review"); fits saved before 13:12 show
  2f7e567 (HEAD before that commit), later ones 917b222 or dc45d5d.
- percell (launched about 14:35) and radius (about 15:10): 4710751 plus the
  one-record-per-cell option of c75b1c7 (the option is inactive unless
  `--thin-one-per-cell` is given). No other package change between 4710751 and dc45d5d.
- root-weevil rerun (16:05): dc45d5d plus the uncommitted switch of
  `config.Insect_list["Root_Weevil"]` to `Root_Weevil_est_EPPO.gpkg` and the new
  `git_dirty` provenance field (recorded as True); both are in the commit that
  follows dc45d5d. Tag `revision-runs-2026-10-13` marks that commit.
