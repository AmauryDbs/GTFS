PY=python
PIP=$(PY) -m pip

.ONESHELL:

setup:
$(PY) -m venv .venv
. .venv/bin/activate || .venv\\Scripts\\activate
$(PIP) install --upgrade pip
$(PIP) install -r requirements.txt
@echo "OK. Activez l'environnement: source .venv/bin/activate"

lint:
. .venv/bin/activate || .venv\\Scripts\\activate
ruff check src
black --check src
isort --check-only src

fmt:
. .venv/bin/activate || .venv\\Scripts\\activate
black src
isort src

ingest:
. .venv/bin/activate || .venv\\Scripts\\activate
$(PY) -m transport_analytics.ingest.gtfs data/raw/gtfs/$(GTFS)

derived:
. .venv/bin/activate || .venv\\Scripts\\activate
$(PY) -m transport_analytics.analytics.kpis

notebooks:
. .venv/bin/activate || .venv\\Scripts\\activate
jupytext --to ipynb notebooks/*.py
@echo "Lance Jupyter: jupyter lab"

test:
. .venv/bin/activate || .venv\\Scripts\\activate
pytest -q
