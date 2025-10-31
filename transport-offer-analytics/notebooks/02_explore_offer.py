# %% [markdown]
# # 02 — Exploration de l'offre (filtres + aperçu)

# %%
from pathlib import Path

import plotly.express as px
import polars as pl
from ipywidgets import Dropdown, VBox

from transport_analytics.config import PARQUET_CORE

routes = pl.read_parquet(PARQUET_CORE / "routes_core.parquet")
headways_path = Path("data/derived/headways_by_route_daytype.parquet")
headways = pl.read_parquet(headways_path) if headways_path.exists() else pl.DataFrame()

mode_filter = Dropdown(options=["Tous", "Bus", "Métro", "Tram", "Rail"], value="Tous", description="Mode:")


def refresh(_=None) -> None:
    df = headways
    if df.height > 0:
        fig = px.bar(df.to_pandas(), x="route_id", y="avg_headway_min", color="timeband", barmode="group")
        fig.show()
    else:
        print("Lancez d'abord le calcul des KPI (make derived).")


ui = VBox([mode_filter])
refresh()
