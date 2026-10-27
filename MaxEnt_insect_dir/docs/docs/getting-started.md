# Getting started

## Install

```bash
conda activate postdoc
cd MaxEnt_insect_dir
pip install -e ".[dev]"
```

## Smoke test

```bash
python -m maxent_insect_dir.run --pathways SSP_245 --insects Spotted_Lanternfly --smoke-test
```

## Unit tests

```bash
pytest -q
```
