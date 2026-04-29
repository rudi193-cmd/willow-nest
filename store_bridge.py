"""
store_bridge.py — Willow SOIL store wrapper for Nest pipeline state.
b17: B2DA2  ΔΣ=42

Reads/writes file records in files/store as files move through pipeline stages.
Talks to Willow via MCP (willow.sh) — SAP gate enforced on every call.
No direct Python import of WillowStore.
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Locate soil_client — canonical path in willow-1.9/sap/clients/,
# falling back to a copy bundled next to this file.
_WILLOW_ROOT = Path(os.environ.get("WILLOW_ROOT", Path(__file__).parent.parent / "willow-1.9"))
_SAP_CLIENTS = _WILLOW_ROOT / "sap" / "clients"
if _SAP_CLIENTS.exists() and str(_WILLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(_WILLOW_ROOT))

try:
    from sap.clients.soil_client import SoilClient
except ImportError:
    # Bundled copy next to this file (for users without willow-1.9 on path)
    _local = Path(__file__).parent / "soil_client.py"
    if _local.exists():
        import importlib.util as _ilu
        _spec = _ilu.spec_from_file_location("soil_client", _local)
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        SoilClient = _mod.SoilClient
    else:
        SoilClient = None  # type: ignore

APP_ID = "willow-nest"
FILES_COLLECTION = "files/store"

_client: "SoilClient | None" = None


def _get_client() -> "SoilClient | None":
    global _client
    if _client is None and SoilClient is not None:
        _client = SoilClient(app_id=APP_ID)
    return _client


def gen_b17(length: int = 5) -> str:
    """Generate a b17-compatible short ID (hex, uppercased)."""
    return uuid.uuid4().hex[:length].upper()


def write_file_record(
    b17: str,
    path: str,
    filename: str,
    track: str,
    status: str = "sorted",
    moved_to: "str | None" = None,
) -> str:
    """Create or update a file record in files/store. Returns b17."""
    client = _get_client()
    if not client:
        sys.stderr.write("[store_bridge] Willow unavailable — store_bridge is a no-op\n")
        return b17
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
    client.put(FILES_COLLECTION, record, record_id=b17)
    return b17


def update_status(b17: str, status: str, extra: "dict | None" = None) -> None:
    """Update nest_status on an existing files/store record."""
    client = _get_client()
    if not client:
        sys.stderr.write("[store_bridge] Willow unavailable — update_status skipped\n")
        return
    existing = client.get(FILES_COLLECTION, b17)
    if not existing:
        raise KeyError(f"No files/store record for b17={b17}")
    existing["nest_status"] = status
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    if extra:
        existing.update(extra)
    client.put(FILES_COLLECTION, existing, record_id=b17)


def get_record(b17: str) -> "dict | None":
    client = _get_client()
    if not client:
        return None
    return client.get(FILES_COLLECTION, b17)
