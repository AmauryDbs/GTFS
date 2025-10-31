# GTFS Local Analytics Toolkit

## Aperçu (FR)

Cet entrepôt fournit un outil **local-first** pour analyser l'offre de transport à partir de jeux de données GTFS et de données ouvertes du territoire. Les pipelines actuels s'exécutent avec la bibliothèque standard de Python afin de fonctionner dans des environnements restreints, tout en conservant une fine couche FastAPI optionnelle pour une intégration ultérieure.

### Organisation du dépôt

```
backend/    Bibliothèque Python et point d'entrée FastAPI optionnel
frontend/   Socle React + Vite pour l'interface utilisateur locale
data/       Stockage des feeds ingérés, indicateurs dérivés et exports (ignoré par Git)
scripts/    Scripts en ligne de commande pour orchestrer les workflows
```

### Exécution des scripts

```bash
python scripts/ingest_gtfs.py chemin/vers/feed.zip --output data
python scripts/compute_headways.py <hash_feed> --data-dir data
python scripts/compute_accessibility.py <hash_feed> chemin/vers/zones.geojson --data-dir data
```

Ces commandes génèrent des instantanés JSON et mettent à jour l'arborescence `data/`. Vous pouvez surcharger ce répertoire via la variable d'environnement `GTFS_DATA_DIR`.

### API FastAPI optionnelle

Si vous souhaitez exposer une API locale :

```bash
pip install fastapi uvicorn
uvicorn gtfs_analytics.app.main:create_app --factory --reload
```

### Frontend

Le dossier `frontend/` contient le squelette Vite historique (React + Tailwind + MapLibre). Il n'est pas activé par défaut dans les tests et peut être développé indépendamment pour construire l'interface de visualisation.

### Tests

Les tests automatisés résident dans `backend/tests`. Exécution :

```bash
cd backend
pytest
```

### Travail sans accès distant

Dans certains environnements (par exemple sur cette plateforme d'entraînement), aucun `remote` Git n'est configuré et les téléchargements réseau peuvent être bloqués. Les commandes `git fetch origin` échouent alors avec `fatal: 'origin' does not appear to be a git repository`. Pour collaborer malgré tout :

1. Travaillez sur la branche locale existante (`work` par défaut).
2. Créez des branches locales supplémentaires via `git switch -c ma-branche` si besoin.
3. Exportez vos modifications avec `git format-patch` ou `git bundle` afin de les réappliquer plus tard sur un dépôt distant accessible.

Cette approche conserve un historique propre et facilite le partage une fois la connexion rétablie.

### Licence

MIT.

## Overview (EN)

This repository provides a local-first toolkit for evaluating public transport service offers from GTFS feeds and open territorial datasets. The current implementation focuses on lightweight, dependency-free data pipelines that can run in restricted environments. A thin optional FastAPI layer is kept for future integration but is not required to execute the analytics scripts or the automated tests.

### Project layout

```
backend/    Pure-Python analytics library and optional FastAPI entrypoint
frontend/   React + Vite single-page application scaffold (not exercised in tests)
data/       Storage for ingested feeds, derived indicators, and exports (git-ignored)
scripts/    Helper CLI entry points for orchestrating local workflows
```

### Python environment

Run the pipelines directly without third-party packages:

```bash
python scripts/ingest_gtfs.py path/to/feed.zip --output data
python scripts/compute_headways.py <feed_hash> --data-dir data
python scripts/compute_accessibility.py <feed_hash> path/to/zones.geojson --data-dir data
```

### Optional FastAPI API

Install FastAPI manually and start the server if you need HTTP endpoints:

```bash
pip install fastapi uvicorn
uvicorn gtfs_analytics.app.main:create_app --factory --reload
```

### Frontend

The `frontend/` directory still contains the previous Vite scaffold. It is untouched by the current tests and can be iterated independently if you need a UI layer.

### Tests

Automated tests live under `backend/tests`. Execute them with:

```bash
cd backend
pytest
```

### Working without remotes

In restricted sandboxes there is no configured Git `remote` and outbound traffic can be blocked, so commands like `git fetch origin` fail with `fatal: 'origin' does not appear to be a git repository`. To collaborate under these constraints:

1. Keep working on the current local branch (`work` by default) or create new ones via `git switch -c my-branch`.
2. Export your commits with `git format-patch` or `git bundle` to share them once connectivity is restored.
3. Apply those artifacts on another machine that can reach the canonical repository.

This keeps history auditable even when direct pushes are impossible.

### License

MIT.
