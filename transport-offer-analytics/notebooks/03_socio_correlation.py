# %% [markdown]
# # 03 — Socio ↔ Offre (corrélations MVP)

# %%
from pathlib import Path

import polars as pl

headways_path = Path("data/derived/headways_by_route_daytype.parquet")
if headways_path.exists():
    headways = pl.read_parquet(headways_path)
    display(headways.head())
else:
    print("Calculez les KPI via `make derived` puis ajoutez vos données socio-territoriales.")

print("Placeholder : chargez vos socio (maille_id -> population, emploi, etc.) et rejoignez-les.")
