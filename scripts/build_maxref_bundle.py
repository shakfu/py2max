#!/usr/bin/env python3
"""Generate the prebuilt maxref JSON bundle shipped with py2max.

Run this on a machine that has Max installed (macOS/Windows). It walks every
``.maxref.xml`` file via the existing ``py2max.maxref`` parser and writes a
single JSON file at::

    py2max/maxref/data/bundle.json.gz

On machines without Max (e.g. Linux CI), ``MaxRefCache`` falls back to this
bundle so inlet/outlet counts, type introspection, and ``Box.help()`` keep
working.

Schema::

    {
      "version": 1,
      "object_count": <int>,
      "objects": {
        "<name>": {
          "_category": "max" | "msp" | "jit" | "m4l",
          ...parser output from MaxRefCache.get_object_data...
        }
      }
    }

Usage::

    uv run python scripts/build_maxref_bundle.py
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

# Ensure imports resolve against the source tree rather than an installed wheel.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from py2max.maxref.parser import MaxRefCache  # noqa: E402


BUNDLE_PATH = REPO_ROOT / "py2max" / "maxref" / "data" / "bundle.json.gz"


def main() -> int:
    cache = MaxRefCache()
    refdict = cache.refdict
    category_map = cache.category_map

    if not refdict:
        print(
            "ERROR: no .maxref.xml files found. Run this on macOS/Windows "
            "with Max installed.",
            file=sys.stderr,
        )
        return 1

    names = sorted(refdict.keys())
    print(f"Found {len(names)} Max objects; parsing...", file=sys.stderr)

    objects: dict = {}
    missing: list[str] = []
    for i, name in enumerate(names, 1):
        if i % 200 == 0 or i == len(names):
            print(f"  [{i}/{len(names)}]", file=sys.stderr)
        data = cache.get_object_data(name)
        if data is None:
            missing.append(name)
            continue
        entry = dict(data)
        entry["_category"] = category_map.get(name, "")
        objects[name] = entry

    if missing:
        print(
            f"WARNING: {len(missing)} objects failed to parse: {missing[:10]}"
            f"{'...' if len(missing) > 10 else ''}",
            file=sys.stderr,
        )

    bundle = {
        "version": 1,
        "object_count": len(objects),
        "objects": objects,
    }

    BUNDLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(bundle, separators=(",", ":")).encode("utf-8")
    with gzip.open(BUNDLE_PATH, "wb", compresslevel=9) as f:
        f.write(payload)
    size_kb = BUNDLE_PATH.stat().st_size / 1024
    print(
        f"Wrote {BUNDLE_PATH.relative_to(REPO_ROOT)} "
        f"({len(objects)} objects, {size_kb:.0f} KiB)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
