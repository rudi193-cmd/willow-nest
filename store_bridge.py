"""
store_bridge.py — WillowStore wrapper for Nest pipeline state.
b17: B2DA2  ΔΣ=42

Reads/writes file records in files/store as files move through pipeline stages.
Imports WillowStore directly from willow-1.9 (WILLOW_19_ROOT env var or sibling dir).
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Locate willow-1.9 root
_WILLOW_ROOT = Path(os.environ.get(
    "WILLOW_19_ROOT",
    str(Path(__file__).parent.parent / "willow-1.9")
))
if str(_WILLOW_ROOT / "core") not in sys.path:
    sys.path.insert(0, str(_WILLOW_ROOT / "core"))

from willow_store import WillowStore  # noqa: E402

STORE_ROOT = os.environ.get(
    "WILLOW_STORE_ROOT",
    str(Path.home() / ".willow" / "store")
)
FILES_COLLECTION = "files/store"

_store = WillowStore(STORE_ROOT)


def gen_b17(length: int = 5) -> str:
    """Generate a b17-compatible short ID (hex, uppercased)."""
    return uuid.uuid4().hex[:length].upper()


def write_file_record(
    b17: str,
    path: str,
    filename: str,
    track: str,
    status: str = "sorted",
    moved_to: str | None = None,
) -> str:
    """Create or update a file record in files/store. Returns b17."""
    record = {
        "b17": b17,
        "path": path,
        "filename": filename,
        "track": track,
        "nest_status": status,
        "indexed_at": datetime.now(timezone.utc).isoformat(),
    }
    if moved_to:
        record["moved_to"] = moved_to
    _store.put(FILES_COLLECTION, record, record_id=b17)
    return b17


def update_status(b17: str, status: str, extra: dict | None = None) -> None:
    """Update nest_status on an existing files/store record."""
    existing = _store.get(FILES_COLLECTION, b17)
    if not existing:
        raise KeyError(f"No files/store record for b17={b17}")
    existing["nest_status"] = status
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    if extra:
        existing.update(extra)
    _store.put(FILES_COLLECTION, existing, record_id=b17)


def get_record(b17: str) -> dict | None:
    return _store.get(FILES_COLLECTION, b17)
