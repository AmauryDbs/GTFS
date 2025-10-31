# ---
# jupytext:
#   formats: ipynb,py:percent
#   text_representation:
#     extension: .py
#     format_name: percent
# ---
# %% [markdown]
# # 01 — Ingestion GTFS → Parquet (core)
# Déposez `data/raw/gtfs/monreseau.zip` puis exécutez la cellule suivante.

# %%
from pathlib import Path

from transport_analytics.ingest.gtfs import ingest_gtfs

zip_path = Path("data/raw/gtfs/monreseau.zip")  # changez si besoin
ingest_gtfs(zip_path)

# %% [markdown]
# ✅ Les tables Parquet sont dans `data/parquet/core`.
