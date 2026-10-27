# MaxEnt invasive insect habitat modeling

Python package for Maximum Entropy (MaxEnt) species distribution models of invasive
insect pests under current and future climate (WorldClim SSPs). This is the FSU
modeling codebase for USDA NIFA Accession **1028629** (FAMU lead; FSU PI Olmo
Zavala-Romero).

Scientific write-up: Chouhan, Zavala-Romero & Haseeb (2026),
[bioRxiv 10.64898/2026.04.18.719331](https://doi.org/10.64898/2026.04.18.719331).

## Layout

```text
MaxEnt_insect_dir/
├── maxent_insect_dir/     # installable package (pipeline + spatial_kde)
├── tests/                 # unit tests (Boyce index, thinning, config)
├── reports/               # analysis notes and figures
├── notebooks/             # exploratory notebooks (gitignored)
├── models/                # optional local model cache
├── docs/                  # MkDocs scaffold
├── pyproject.toml
└── requirements.txt
```

## Environment

Preferred lab env (has `elapid` and geospatial stack):

```bash
source ~/anaconda3/etc/profile.d/conda.sh
conda activate postdoc
cd MaxEnt_insect_dir
pip install -e ".[dev]"
```

Alternatively with the default uv env (install runtime deps first):

```bash
uv pip install --python /home/olmozavala/uv/envs/eoasweb -e ".[dev]"
```

Data defaults to `/data/Maxent/data`. Override with:

```bash
export MAXENT_DATA_ROOT=/path/to/data
export MAXENT_RESULTS_ROOT=/path/to/results
```

## Run experiments

```bash
# Habitat-grid default: all species, SSP_245, feature=lph, beta=1.5, m=0.25
python -m maxent_insect_dir.run --pathways SSP_245

# Performance table (CBI/AUC vs m): lph, beta 2.0, five mixing values, 20 repeats.
# See docs/paper_performance_table.md and ../scripts/rerun_paper_m_table.sh
python -m maxent_insect_dir.run --pathways SSP_245 \
  --feature-types lph \
  --beta-multipliers 2.0 \
  --bias-mix 0 0.25 0.5 0.75 1 \
  --repeats 20 \
  --skip-projections

# Smoke test (fast, skips projections; write results somewhere writable)
MAXENT_RESULTS_ROOT=/tmp/maxent_smoke_results \
  python -m maxent_insect_dir.run --pathways SSP_245 --insects Spotted_Lanternfly --smoke-test

# Or: make smoke

# Full sensitivity grid (matches paper-scale sweeps)
python -m maxent_insect_dir.run --pathways SSP_245 SSP_370 \
  --insects Brown_Marmorated_Stink_bug Corn_Earworm Root_Weevil Spongy_Moth Spotted_Lanternfly \
  --feature-types l lq lqh lph lqhp lqhpt \
  --beta-multipliers 0.5 1.0 1.5 2.0 2.5 \
  --bias-mix 0.25 \
  --repeats 4
```

After install, the console script `maxent-insects` is equivalent to
`python -m maxent_insect_dir.run`.

## Tests

```bash
pytest -q
```

## Species keys

| Key | Scientific name |
|-----|-----------------|
| `Brown_Marmorated_Stink_bug` | *Halyomorpha halys* |
| `Corn_Earworm` | *Helicoverpa zea* |
| `Root_Weevil` | *Diaprepes abbreviatus* |
| `Spongy_Moth` | *Lymantria dispar* |
| `Spotted_Lanternfly` | *Lycorma delicatula* |

(`Spooted_Lanternfly` remains as a deprecated alias.)

## Outputs

Results are written under `$MAXENT_RESULTS_ROOT/<SSP>/<insect>/<m>/<feature>/<beta>/...`
including `current.tif`, future projections, optional plots, and `experiment_states.pkl`.
