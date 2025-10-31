# Transport Offer Analytics

## Description
Transport Offer Analytics est un projet local-first pour analyser une offre de transport à partir d'un jeu de données GTFS compressé (`.zip`). Le pipeline ingère les fichiers GTFS, les normalise en tables Parquet, applique des règles d'enrichissement (jours-types, typologies de lignes, plages horaires), rattache l'offre à des mailles territoriales et calcule des indicateurs de base. Les résultats sont explorables dans des notebooks Jupyter interactifs.

### Schéma d'architecture (texte)
1. **Ingestion** : lecture du GTFS (`zip`) → validation → tables Parquet « core » (Polars/Arrow).
2. **Enrichissement** : application des règles YAML (jours-types, typologies) et calage sur des plages horaires communes.
3. **Stockage analytique** : structuration en Parquet/GeoParquet, accessible via DuckDB + extension spatiale.
4. **Jointures spatiales** : rattachement des arrêts et segments aux mailles territoriales (GeoParquet/GeoPackage).
5. **KPI & analyses** : calculs de trips/h, headways approximatifs, amplitudes, proxy VH-km, couverture territoriale et corrélations socio ↔ offre.
6. **Exploration** : notebooks Jupyter avec `ipywidgets`, cartes simples et exports (CSV/Parquet).

### Limites (MVP)
- Calcul des headways à partir des premiers arrêts uniquement (approximation basée sur `stop_times`).
- Gestion simplifiée des jours-types (peu ou pas d'exceptions calendaires complexes).
- Jointures spatiales focalisées sur les arrêts (segments à implémenter).
- Corrélations socio ↔ offre illustrées par des placeholders, à compléter avec vos propres données.

## Prérequis
- Python 3.11+
- `make`

## Setup rapide
1. `make setup`
2. Déposez un fichier GTFS dans `data/raw/gtfs/monreseau.zip`
3. `make ingest GTFS=monreseau.zip`
4. `make notebooks`

## Commandes Make utiles
- `make setup` : crée l'environnement virtuel et installe les dépendances.
- `make lint` : exécute `ruff`, `black --check`, `isort --check-only` sur `src/`.
- `make fmt` : applique `black` et `isort`.
- `make ingest GTFS=<fichier>` : lance l'ingestion GTFS.
- `make derived` : calcule les indicateurs principaux (Parquet dans `data/derived/`).
- `make notebooks` : convertit les scripts Jupytext en `.ipynb` et rappelle comment lancer Jupyter Lab.
- `make test` : exécute la suite `pytest`.

## Notes de performances
- Les traitements reposent sur **Polars**, **Apache Arrow** et des sorties **Parquet**, garantissant des IO rapides et un usage mémoire efficient.
- **DuckDB** sert de moteur analytique local et, avec son extension spatiale, permet les jointures géographiques à haute performance.

## Notes spatiales
- Les jointures s'appuient sur DuckDB Spatial (`INSTALL spatial; LOAD spatial;`) pour exploiter des GeoParquet ou GeoPackage.
- Les jeux de référence géographiques sont attendus dans `data/parquet/geo/`.

## Avertissement
Les headways sont calculés de manière approximative à partir des heures de départ (`stop_times`) au premier arrêt de chaque trajet. Ajustez selon la granularité désirée.
