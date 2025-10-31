Backend Python léger alimentant l'outil d'analyse GTFS. Le code de traitement repose volontairement sur la bibliothèque standard de Python afin de s'exécuter dans des environnements contraints. Un point d'entrée FastAPI optionnel est disponible si vous installez manuellement les dépendances correspondantes.

## Utilisation (FR)

```bash
python scripts/ingest_gtfs.py chemin/vers/feed.zip --output data
python scripts/compute_headways.py <hash_feed>
python scripts/compute_accessibility.py <hash_feed> chemin/vers/zones.geojson
```

Par défaut, l'application lit et écrit ses artefacts sous `data/` à la racine du dépôt. Utilisez la variable d'environnement `GTFS_DATA_DIR` pour modifier cet emplacement. Pour l'API :

```bash
python -m pip install fastapi uvicorn  # optionnel, seulement pour la couche API
uvicorn gtfs_analytics.app.main:create_app --factory --reload
```

## Usage (EN)

Lightweight Python backend powering the GTFS analytics toolkit. The core data processing code purposefully avoids third-party dependencies so that it can run in sandboxed environments. An optional FastAPI entrypoint is available if you install the relevant extras manually.

```bash
python scripts/ingest_gtfs.py path/to/feed.zip --output data
python scripts/compute_headways.py <feed_hash>
python scripts/compute_accessibility.py <feed_hash> path/to/zones.geojson
```

The application reads and writes artefacts under the `data/` directory at the repository root by default. Override with the `GTFS_DATA_DIR` environment variable if needed. To launch the API:

```bash
python -m pip install fastapi uvicorn  # optional, only for the API layer
uvicorn gtfs_analytics.app.main:create_app --factory --reload
```
