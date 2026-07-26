#!/usr/bin/env python3
"""Compare a patch js2max wrote against the patch it was serialized from.

`serialize` describes the whole patcher, so writing the harness produces
something that looks like the harness. That resemblance is the point -- it is a
round-trip fidelity check -- but it is only reassuring if the differences are
actually measured. This measures them.

Usage:
    python scripts/check_js2max_roundtrip.py <written.maxpat> [<source.maxpat>]

The source defaults to the harness. Reports, per box: keys that were lost, keys
that were added, and values that changed. Exit code is 1 if anything was lost.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "js2max" / "max" / "v8-harness.maxpat"

# Differences that are expected and carry no information.
IGNORED = {
    # ids are reassigned positionally on serialize
    "id",
    # the patcher's own window geometry is not a box property
    "rect",
}


def boxes(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text())
    return [entry["box"] for entry in data["patcher"].get("boxes", [])]


def key(box: Dict[str, Any]) -> Tuple[str, str]:
    """Identify a box by what survives reserialization: class and text."""
    return (box.get("maxclass", ""), str(box.get("text", "")))


def compare(source: Path, written: Path) -> int:
    src, out = boxes(source), boxes(written)
    print(f"source : {source}  ({len(src)} boxes)")
    print(f"written: {written}  ({len(out)} boxes)\n")

    by_key: Dict[Tuple[str, str], Dict[str, Any]] = {key(b): b for b in out}
    lost_total = 0

    for box in src:
        identity = key(box)
        match = by_key.pop(identity, None)
        label = f"{identity[0]} {identity[1][:40]!r}"
        if match is None:
            print(f"MISSING  {label}")
            lost_total += 1
            continue

        lost = sorted(k for k in box if k not in match and k not in IGNORED)
        added = sorted(k for k in match if k not in box and k not in IGNORED)
        changed = sorted(
            k
            for k in box
            if k in match and k not in IGNORED and box[k] != match[k]
        )
        if not (lost or added or changed):
            print(f"ok       {label}")
            continue

        print(f"DIFF     {label}")
        if lost:
            print(f"           lost:    {', '.join(lost)}")
            lost_total += len(lost)
        if added:
            print(f"           added:   {', '.join(added)}")
        for k in changed:
            print(f"           changed: {k}: {box[k]!r} -> {match[k]!r}")

    extra = list(by_key)
    for identity in extra:
        print(f"EXTRA    {identity[0]} {identity[1][:40]!r}")
    if extra:
        print(
            f"\n{len(extra)} box(es) present only in the written file."
            " Expected if objects were built before writing."
        )

    src_lines = len(json.loads(source.read_text())["patcher"].get("lines", []))
    out_lines = len(json.loads(written.read_text())["patcher"].get("lines", []))
    print(f"\nlines: {src_lines} -> {out_lines}")
    # Only *fewer* lines is a loss. The write demo deliberately adds objects
    # before serializing, so its output is a superset of its input -- counting
    # the growth as loss would report a working demo as broken.
    if out_lines < src_lines:
        lost_total += src_lines - out_lines

    print(f"\n{'FAITHFUL' if lost_total == 0 else f'{lost_total} loss(es)'}")
    return 1 if lost_total else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("written", type=Path, help="the file js2max wrote")
    parser.add_argument("source", type=Path, nargs="?", default=DEFAULT_SOURCE)
    args = parser.parse_args()

    for path in (args.written, args.source):
        if not path.exists():
            print(f"not found: {path}", file=sys.stderr)
            return 2
    return compare(args.source, args.written)


if __name__ == "__main__":
    sys.exit(main())
