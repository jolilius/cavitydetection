#!/usr/bin/env python3
"""
Migrate legacy flat experiment directories to the new runs/ structure.

Usage (from project root):
    ../openevolve/.venv/bin/python openevolve/migrate_legacy.py [--output-root PATH]

Idempotent: already-migrated directories are skipped without error.
Moves all non-runs/ subdirectories under OUTPUT_ROOT to:
    OUTPUT_ROOT/runs/legacy/cavitydetection/<dirname>/
"""

import argparse
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def migrate_legacy(output_root: str) -> None:
    """Move all non-runs/ subdirectories to runs/legacy/cavitydetection/."""
    legacy_dir = os.path.join(output_root, "runs", "legacy", "cavitydetection")
    os.makedirs(legacy_dir, exist_ok=True)

    skip = {"runs", "best", "checkpoints", "logs", "archive"}
    for name in sorted(os.listdir(output_root)):
        if name in skip:
            continue
        src = os.path.join(output_root, name)
        if not os.path.isdir(src):
            continue
        # Only migrate directories that look like prompt experiments
        has_results = os.path.isfile(os.path.join(src, "results.json"))
        has_best = os.path.isfile(os.path.join(src, "best", "best_program_info.json"))
        if not (has_results or has_best):
            continue
        dst = os.path.join(legacy_dir, name)
        if os.path.exists(dst):
            print(f"Skip (already migrated): {name}")
            continue
        try:
            os.rename(src, dst)
        except OSError as e:
            if e.errno == 18:  # EXDEV — cross-device link
                shutil.move(src, str(dst))
            else:
                raise
        print(f"Moved: {name} -> runs/legacy/cavitydetection/{name}")


def regenerate_results(output_root: str) -> None:
    """Regenerate results.json from checkpoints for all migrated experiment dirs.

    For each experiment under runs/legacy/cavitydetection/<name>/ that has a
    checkpoints/ subdir:
      1. Back up existing results.json to results.json.v1 (D-10: always before overwrite).
      2. Call consolidate_experiment() to rebuild results.json from checkpoints.

    Experiments with no checkpoints/ subdir are skipped (Pitfall 5).
    If the legacy dir doesn't exist at all, prints a message and returns cleanly.
    """
    # Import inline to avoid circular imports at module load time
    try:
        from consolidate_results import consolidate_experiment
    except ImportError:
        from .consolidate_results import consolidate_experiment

    legacy_dir = os.path.join(output_root, "runs", "legacy", "cavitydetection")
    if not os.path.isdir(legacy_dir):
        print(f"No legacy directory found at {legacy_dir}, nothing to regenerate.")
        return

    for name in sorted(os.listdir(legacy_dir)):
        exp_dir = os.path.join(legacy_dir, name)
        if not os.path.isdir(exp_dir):
            continue
        # Pitfall 5: only process dirs that have a checkpoints/ subdir
        if not os.path.isdir(os.path.join(exp_dir, "checkpoints")):
            print(f"Skip (no checkpoints/): {name}")
            continue

        results_path = os.path.join(exp_dir, "results.json")
        backup_path = os.path.join(exp_dir, "results.json.v1")

        if os.path.isfile(results_path):
            shutil.copy2(results_path, backup_path)  # D-10: always backup first
            print(f"Backed up: runs/legacy/cavitydetection/{name}/results.json -> results.json.v1")

        try:
            consolidate_experiment(output_dir=exp_dir)
            print(f"Regenerated: runs/legacy/cavitydetection/{name}/results.json")
        except Exception as e:
            print(f"Warning: regeneration failed for {name}: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate legacy flat experiment directories to runs/legacy/cavitydetection/."
    )
    parser.add_argument(
        "--output-root",
        default=os.path.join(SCRIPT_DIR, "openevolve_output"),
        help="Base output directory to migrate (default: openevolve/openevolve_output/)",
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        default=False,
        help=(
            "Regenerate results.json from checkpoints for all migrated experiments; "
            "backs up existing results.json as results.json.v1"
        ),
    )
    args = parser.parse_args()

    output_root = args.output_root
    if not os.path.exists(output_root):
        sys.exit(f"Output root not found: {output_root}")

    migrate_legacy(output_root)
    print("Migration complete.")

    if args.regenerate:
        print("Regenerating results.json from checkpoints...")
        regenerate_results(output_root)
        print("Regeneration complete.")


if __name__ == "__main__":
    main()
