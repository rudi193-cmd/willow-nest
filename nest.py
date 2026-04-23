"""
nest.py — Willow Nest: intake consent layer + pipeline runner.
b17: B2DA2  ΔΣ=42

Usage:
  python3 nest.py              # scan default drop zones, show consent, run on confirm
  python3 nest.py --dry-run    # show what would happen, no moves
  python3 nest.py --run-pipeline <b17>  # run pipeline stages for an already-sorted file
  python3 nest.py --drain      # run pipeline on all sorted records in files/store

Drop zones:
  ~/Desktop/Nest/
  ~/Ashokoa/Nest/processed/
"""

import argparse
import sys
from pathlib import Path

from classify import classify
from router import propose, route_file, TRACK_TO_NEXT_STAGE
from store_bridge import get_record, update_status

NEST_DIRS = [
    Path.home() / "Desktop" / "Nest",
    Path.home() / "Ashokoa" / "Nest" / "processed",
]

PIPELINE_STAGES = {
    "compost":  ("pipeline.compost",  "run"),
    "scrub":    ("pipeline.scrub",    "run"),
    "promote":  ("pipeline.promote",  "run"),
    "archive":  ("pipeline.archive",  "run"),
}

TRACK_PIPELINE = {
    # Personal files — sort to ~/personal/, then process
    "journal":         ["compost", "promote"],
    "legal":           ["scrub"],           # stays in personal/legal/ — no second move
    "knowledge":       ["promote"],
    "narrative":       ["compost", "promote"],
    "photos_personal": [],                  # already in personal/photos/personal/
    "photos_camera":   [],                  # already in personal/photos/camera/
    "screenshots":     [],                  # already in personal/photos/screenshots/
    # Agent artifacts — large/bulk go to cold storage
    "handoffs":        ["compost", "promote"],
    "specs":           ["compost", "promote"],
    "unknown":         [],
}


def _run_stage(stage_name: str, b17: str) -> dict:
    module_path, fn_name = PIPELINE_STAGES[stage_name]
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, fn_name)(b17)


def run_pipeline(b17: str) -> list[dict]:
    record = get_record(b17)
    if not record:
        print(f"  ERROR: no record for {b17}")
        return []
    track = record.get("track", "unknown")
    stages = TRACK_PIPELINE.get(track, [])
    results = []
    for stage in stages:
        print(f"  [{stage}] {b17} ...", end=" ", flush=True)
        result = _run_stage(stage, b17)
        status = result.get("status", result.get("error", "?"))
        print(status)
        results.append(result)
        if "error" in result:
            print(f"    !! {result['error']}")
            break
    return results


def scan_drop_zones() -> list[Path]:
    files = []
    for d in NEST_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.iterdir()):
            if f.is_file() and not f.name.startswith("."):
                files.append(f)
    return files


def show_consent(files: list[Path]) -> None:
    print(f"\n{'─'*60}")
    print(f"  NEST — {len(files)} file(s) detected")
    print(f"{'─'*60}")
    for f in files:
        p = propose(f)
        track = p["track"]
        dest = p["proposed_dest"] or "QUARANTINE"
        stages = " → ".join(TRACK_PIPELINE.get(track, ["?"]))
        print(f"  {f.name}")
        print(f"    track:  {track}")
        print(f"    dest:   {dest}")
        print(f"    stages: {stages}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Willow Nest file intake")
    parser.add_argument("--dry-run", action="store_true", help="Show plan, no moves")
    parser.add_argument("--run-pipeline", metavar="B17", help="Run pipeline for sorted b17")
    parser.add_argument("--drain", action="store_true", help="Run pipeline on all sorted records")
    args = parser.parse_args()

    # --- Pipeline mode ---
    if args.run_pipeline:
        b17 = args.run_pipeline.upper()
        print(f"\nRunning pipeline for {b17}...")
        run_pipeline(b17)
        return

    # --- Drain mode ---
    if args.drain:
        print("\nDrain mode — checking files/store for sorted records...")
        from store_bridge import _store, FILES_COLLECTION
        # Iterate via search — get all records with nest_status=sorted
        # Use direct store search (no MCP needed)
        try:
            records = _store.search(FILES_COLLECTION, "sorted")
        except Exception as e:
            print(f"  Store search failed: {e}")
            return
        sorted_records = [r for r in records if r.get("nest_status") == "sorted"]
        print(f"  {len(sorted_records)} sorted record(s) to process")
        for rec in sorted_records:
            b17 = rec.get("b17", "?")
            print(f"\n{b17} — {rec.get('filename', '?')} [{rec.get('track', '?')}]")
            run_pipeline(b17)
        return

    # --- Standard intake mode ---
    files = scan_drop_zones()
    if not files:
        print("\nNest is empty. Drop files into:")
        for d in NEST_DIRS:
            print(f"  {d}")
        return

    show_consent(files)

    if args.dry_run:
        print("  [dry-run] No files moved.\n")
        return

    answer = input("Proceed? [y/N] ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return

    print()
    results = []
    quarantined = []
    for f in files:
        print(f"  → {f.name}", end=" ", flush=True)
        result = route_file(f)
        b17 = result["b17"]
        track = result["track"]
        print(f"[{track}] {b17}")

        if track == "unknown":
            quarantined.append(f.name)
            continue

        pipeline_results = run_pipeline(b17)
        results.append((b17, result, pipeline_results))

    print(f"\n{'─'*60}")
    print(f"  Done. {len(results)} filed, {len(quarantined)} quarantined.")
    if quarantined:
        print("  Quarantined (manual review needed):")
        for name in quarantined:
            print(f"    {name}")
    print()


if __name__ == "__main__":
    main()
