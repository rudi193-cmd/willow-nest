---
b17: WNST1
title: Security Audit — willow-nest
date: 2026-05-06
auditor: Hanuman (Claude Code, Sonnet 4.6)
status: open
---

# Security Audit — willow-nest

Part of Level 2 full-fleet security audit. willow-nest — pipeline processor for Willow system artifacts. Classifies, composts, promotes, and archives files via SOIL store integration.

## Rubric Results

| # | Check | Status | Notes |
|---|---|---|---|
| R1 | SQL injection | N/A | No direct SQL queries |
| R2 | Shell injection | ✅ PASS | No subprocess calls; no shell=True |
| R3 | Path traversal | ✅ PASS | No user-controlled path operations |
| R4 | Hardcoded credentials | ✅ PASS | All paths from env vars (WILLOW_ROOT, CREDENTIALS_FILE) |
| R5 | CORS wildcard | N/A | No HTTP server |
| R6 | XSS | N/A | No HTML rendering |
| R7 | Unsigned code execution | ⚠️ WARN | See P2: exec_module on bundled soil_client.py; importlib.import_module on hardcoded stage names |
| R8 | Missing auth on APIs | N/A | No webhook/API receiver |
| R9 | Bare except swallowing errors | ✅ PASS | Exception handling logs or propagates; no silent swallows found |
| R10 | Predictable temp paths | ✅ PASS | No temp file creation |
| R11 | Race conditions | ✅ PASS | No shared mutable state; SOIL writes are append-only |
| R12 | safe_integration.py status() | ❌ MISSING | No safe_integration.py present |
| R13 | Entry point importable | ✅ PASS | `nest.py` CLI pattern; imports clean |
| R14 | requirements.txt pinned | N/A | No external runtime dependencies; stdlib + SOIL client only |
| R15 | No hardcoded dev paths | ✅ PASS | All paths use env vars or Path.home()/relative anchors |

## Findings

### P2: WN-EXEC-01 — exec_module on bundled soil_client.py

**Severity:** P2
**Status:** Open
**File:** `store_bridge.py:29-32`

```python
_spec = _ilu.spec_from_file_location("soil_client", _local)
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
```

The path `_local = Path(__file__).parent / "soil_client.py"` is hardcoded relative to the module — not user-controlled. However, if an attacker can write to the repo directory (e.g., via a compromised dependency or supply-chain attack), they can inject arbitrary code that executes with the user's privileges at import time. Low blast radius in normal operation; worth noting as a foothold risk.

**Recommended fix:** Prefer the `sys.path.insert` fallback over exec_module, or verify the file hash before loading.

---

### P2: WN-SAP-01 — No safe_integration.py

**Severity:** P2
**Status:** Open

No `safe_integration.py` present. willow-nest processes and promotes artifacts through the SOIL store — SAFE integration would gate which pipeline runs are authorized.

---

## Strengths

- **Pipeline stages are fully hardcoded.** `PIPELINE_STAGES` and `TRACK_PIPELINE` dicts are static — no user input can select or inject a module name.
- **No subprocess usage.** All pipeline work is pure Python; no shell calls.
- **No external runtime deps.** stdlib + optional SOIL client; minimal attack surface.
- **Path handling is safe.** All paths derived from `Path(__file__).parent` or env vars; no user-supplied paths reach filesystem operations.
