#!/usr/bin/env python3
"""Recursively rename all files in docs directory to lowercase.

This script walks through the docs/ directory and renames all files
and directories to lowercase, handling name conflicts gracefully.

Usage:
    python scripts/lowercase_docs.py [--dry-run] [--verbose]

Options:
    --dry-run    Show what would be renamed without actually renaming
    --verbose    Show detailed output for each operation
"""

import argparse
import sys
from pathlib import Path


def lowercase_name(path: Path) -> Path:
    """Get the lowercase version of a path.

    Args:
        path: Path to convert to lowercase

    Returns:
        New path with lowercase name
    """
    return path.parent / path.name.lower()


def rename_to_lowercase(root_dir: Path, dry_run: bool = False, verbose: bool = False) -> tuple[int, int, int]:
    """Recursively rename files and directories to lowercase.

    Args:
        root_dir: Root directory to start renaming from
        dry_run: If True, only show what would be renamed
        verbose: If True, show detailed output

    Returns:
        Tuple of (files_renamed, dirs_renamed, duplicates_removed)
    """
    files_renamed = 0
    dirs_renamed = 0
    duplicates_removed = 0

    # Collect all paths first (to avoid issues with renaming during iteration)
    all_paths = list(root_dir.rglob("*"))

    # Sort by depth (deepest first) to rename children before parents
    all_paths.sort(key=lambda p: len(p.parts), reverse=True)

    for path in all_paths:
        # Skip if already lowercase
        if path.name == path.name.lower():
            if verbose:
                print(f"  Skip (already lowercase): {path.relative_to(root_dir)}")
            continue

        new_path = lowercase_name(path)

        # On case-insensitive filesystems, path.samefile(new_path) will be True
        # if they refer to the same file with different casing
        try:
            is_same_file = path.samefile(new_path)
        except (OSError, FileNotFoundError):
            is_same_file = False

        # Check if target already exists as a different file (true duplicate)
        if new_path.exists() and not is_same_file:
            # Lowercase version exists as a separate file, remove the uppercase version
            action = "Would remove duplicate" if dry_run else "Removing duplicate"
            print(f"{action}: {path.relative_to(root_dir)} (lowercase version exists)")
            if not dry_run:
                if path.is_file():
                    path.unlink()
                elif path.is_dir() and not list(path.iterdir()):
                    # Only remove empty directories
                    path.rmdir()
                else:
                    print(f"  ⚠ Warning: Directory not empty, skipping: {path.relative_to(root_dir)}")
                    continue
            duplicates_removed += 1
            continue

        # Perform rename
        if path.is_file():
            action = "Would rename file" if dry_run else "Renaming file"
            print(f"{action}: {path.relative_to(root_dir)} -> {new_path.name}")
            if not dry_run:
                path.rename(new_path)
            files_renamed += 1
        elif path.is_dir():
            action = "Would rename dir " if dry_run else "Renaming dir "
            print(f"{action}: {path.relative_to(root_dir)} -> {new_path.name}")
            if not dry_run:
                path.rename(new_path)
            dirs_renamed += 1

    return files_renamed, dirs_renamed, duplicates_removed


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Recursively rename all files in docs directory to lowercase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be renamed without actually renaming",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed output for each operation",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=None,
        help="Path to docs directory (default: docs/ relative to script location)",
    )

    args = parser.parse_args()

    # Determine docs directory
    if args.docs_dir:
        docs_dir = args.docs_dir
    else:
        # Assume script is in scripts/ and docs/ is sibling
        script_dir = Path(__file__).parent
        docs_dir = script_dir.parent / "docs"

    # Validate docs directory exists
    if not docs_dir.exists():
        print(f"Error: docs directory not found: {docs_dir}", file=sys.stderr)
        return 1

    if not docs_dir.is_dir():
        print(f"Error: Not a directory: {docs_dir}", file=sys.stderr)
        return 1

    # Show what we're doing
    print("=" * 70)
    if args.dry_run:
        print("DRY RUN - No files will be renamed")
    print(f"Renaming files in: {docs_dir}")
    print("=" * 70)
    print()

    # Perform rename
    files_renamed, dirs_renamed, duplicates_removed = rename_to_lowercase(
        docs_dir,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if args.dry_run:
        print(f"Would rename {files_renamed} files and {dirs_renamed} directories")
        print(f"Would remove {duplicates_removed} duplicates")
    else:
        print(f"Renamed {files_renamed} files and {dirs_renamed} directories")
        print(f"Removed {duplicates_removed} duplicates")

    if files_renamed == 0 and dirs_renamed == 0 and duplicates_removed == 0:
        print("✓ All files and directories already lowercase")

    return 0


if __name__ == "__main__":
    sys.exit(main())
