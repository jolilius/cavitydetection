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

    skip = {"runs"}
    for name in sorted(os.listdir(output_root)):
        if name in skip:
            continue
        src = os.path.join(output_root, name)
        if not os.path.isdir(src):
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


def main():
    parser = argparse.ArgumentParser(
        description="Migrate legacy flat experiment directories to runs/legacy/cavitydetection/."
    )
    parser.add_argument(
        "--output-root",
        default=os.path.join(SCRIPT_DIR, "openevolve_output"),
        help="Base output directory to migrate (default: openevolve/openevolve_output/)",
    )
    args = parser.parse_args()

    output_root = args.output_root
    if not os.path.exists(output_root):
        sys.exit(f"Output root not found: {output_root}")

    migrate_legacy(output_root)
    print("Migration complete.")


if __name__ == "__main__":
    main()
