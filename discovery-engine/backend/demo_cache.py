"""Demo cache — disk-persisted JSON keyed by SHA-256 of source documents.

Designed to make repeat demo runs (same docs uploaded twice) instant for the
LLM-heavy features. Graph extraction and conformance are intentionally NOT
cached — those should always show the live "doing its thing" moment in a demo.

Schema on disk:
{
  "<doc_hash>": {
    "workflows":    [...],
    "object_model": {...},
    "blueprint":    {...},
    "pulse_ai":     {...},
    "cross_doc":    {...}
  },
  ...
}

The cache is loaded on import and saved write-through after every put. Single-
process, single-file — fine for a demo. Don't use this for multi-worker prod.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

CACHE_DIR  = Path(__file__).resolve().parent / "data"
CACHE_FILE = CACHE_DIR / "demo_cache.json"

_FEATURES = ("workflows", "object_model", "blueprint", "pulse_ai", "cross_doc")

_lock: threading.Lock = threading.Lock()
_cache: dict[str, dict[str, Any]] = {}


def _load() -> None:
    global _cache
    if not CACHE_FILE.exists():
        _cache = {}
        return
    try:
        _cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        if not isinstance(_cache, dict):
            _cache = {}
    except Exception:
        # Corrupt file — start fresh, don't crash the server
        _cache = {}


def _save() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(_cache, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CACHE_FILE)


def get(doc_hash: str | None, feature: str) -> Any | None:
    if not doc_hash or feature not in _FEATURES:
        return None
    with _lock:
        return _cache.get(doc_hash, {}).get(feature)


def put(doc_hash: str | None, feature: str, value: Any) -> None:
    if not doc_hash or feature not in _FEATURES:
        return
    with _lock:
        _cache.setdefault(doc_hash, {})[feature] = value
        _save()


def stats() -> dict:
    """Return a summary of what's cached. Used by /api/health."""
    with _lock:
        return {
            "doc_hashes": len(_cache),
            "entries":    sum(len(v) for v in _cache.values()),
            "features":   list(_FEATURES),
        }


_load()
