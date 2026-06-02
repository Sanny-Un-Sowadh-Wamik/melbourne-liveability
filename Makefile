.PHONY: help setup data app test lint format docker-build clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-13s\033[0m %s\n",$$1,$$2}'

setup:  ## Create the venv and install every extra
	uv venv --python 3.11 && uv pip install -e ".[viz,app,dev]"

data:  ## Build the scored liveability dataset (real boundaries + OSM-when-reachable)
	python scripts/build_dataset.py

app:  ## Run the Streamlit dashboard
	streamlit run dashboard/app.py

test:  ## Run the test suite
	pytest -q

lint:  ## Ruff + mypy
	ruff check . && mypy src

format:  ## Auto-format and fix
	ruff format . && ruff check --fix .

docker-build:  ## Build the dashboard image
	docker build -t melb-liveability .

clean:  ## Remove caches
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
