# MaxEnt_insect_dir

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

First module for MaxEnt insect project

## Project Organization

- LICENSE — Open-source license if one is chosen  
- Makefile — Convenience commands for development:  
  - `make requirements` → install dependencies  
  - `make clean` → remove caches  
  - `make lint` / `make format` → code style  
  - `make create_environment` → set up a Conda env  
- README.md — Top-level README for developers  
- dummy_data  
  - climate_data — Avg Bioclim data (19 vars) for SSP_245 (1970–2060)  
  - crop_data — Dominant crop type (mode of 2008–2023 cropland layer at pixel level, 1-min resolution)  
  - elevation — Shapefile for US elevation profile  
  - species_data — Species occurrence (corn earworm, ~100 samples, small dataset for dummy_experiments)
  - test_data — Small dataset for testing  
  - us_shapefile — Shapefile of US boundary  
- dummy_result — Results folder (subdirectories based on experiment settings)  
- models — Trained/serialized models, predictions, summaries  
- notebooks — Jupyter notebooks (`<num>-<initials>-<desc>`)  
- pyproject.toml — Project metadata & tooling config  
- reports — Generated analysis (HTML, PDF, LaTeX, etc.)  
- requirements.txt — Python dependencies  
- setup.cfg — flake8 configuration  
- maxent_insect_dir — Source code  
  - __init__.py — Makes it a package  
  - config.py — Paths, variables, configuration  
  - spatial_kde/ — Spatial kernel density estimation. Used for background point sampling.  
  - continuous_boyce_index/ — Continuous Boyce Index implementation  
  - my_style.mplstyle — Custom matplotlib style  
  - plot_diff_distribution_current_future.py — Plot current vs. future climate distributions (KDE + KS test)  
  - plot_functions.py — Shared plotting functions  
  - prepare_metadata.py — Build metadata before experiments  
  - utilis.py — General utility functions  
  - run_utilis.py — Utilities for run.py  
  - run.py — Main routine to run experiments  


## 🚀 How to Run Experiments

1. **Set up environment**  
   ```bash
   make create_environment
   conda activate maxent_insect_dir
   make requirements

2. **Run experiment**
    ```python
    python maxent_insect_dir/run.py
    ```
