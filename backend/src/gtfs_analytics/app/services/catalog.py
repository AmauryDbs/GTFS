"""Dataset catalog management."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..core.config import get_settings

REGISTRY_FILENAME = "dataset_registry.json"


class DatasetRegistry:
    """Small helper around the registry file."""

    def __init__(self, root: Path | None = None) -> None:
        settings = get_settings()
        self._root = Path(root) if root else settings.data_dir
        self._path = self._root / REGISTRY_FILENAME
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text(json.dumps({"feeds": []}, indent=2))

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> Dict[str, Any]:
        content = self._path.read_text().strip()
        if not content:
            return {"feeds": []}
        return json.loads(content)

    def _write(self, payload: Dict[str, Any]) -> None:
        self._path.write_text(json.dumps(payload, indent=2, default=str))

    def list_feeds(self) -> List[Dict[str, Any]]:
        return list(self.load().get("feeds", []))

    def upsert_feed(self, metadata: Dict[str, Any]) -> None:
        registry = self.load()
        feeds = [feed for feed in registry.get("feeds", []) if feed.get("feed_id") != metadata.get("feed_id")]
        metadata = dict(metadata)
        metadata["updated_at"] = datetime.utcnow().isoformat()
        feeds.append(metadata)
        registry["feeds"] = sorted(feeds, key=lambda item: item["feed_id"])
        self._write(registry)

    def as_json(self) -> str:
        return json.dumps(self.load(), indent=2, default=str)


__all__ = ["DatasetRegistry", "REGISTRY_FILENAME"]
