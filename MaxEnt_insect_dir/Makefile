PROJECT_NAME = MaxEnt_insect_dir
PYTHON_INTERPRETER = python

.PHONY: requirements clean test smoke lint format help

## Install package and dependencies
requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip
	$(PYTHON_INTERPRETER) -m pip install -e ".[dev]"

## Delete compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +

## Run unit tests
test:
	pytest -q

## Fast end-to-end smoke test (requires /data/Maxent read access)
smoke:
	MAXENT_RESULTS_ROOT=/tmp/maxent_smoke_results \
	$(PYTHON_INTERPRETER) -m maxent_insect_dir.run --pathways SSP_245 --insects Spotted_Lanternfly --smoke-test

## Format source code with black
format:
	black --config pyproject.toml maxent_insect_dir tests

## Lint with ruff
lint:
	ruff check maxent_insect_dir tests

.DEFAULT_GOAL := help

help:
	@echo "make requirements | test | smoke | format | lint | clean"
