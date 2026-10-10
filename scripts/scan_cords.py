#!/usr/bin/env python3
"""Validate every cord in a folder of Max-written patches; report what py2max flags.

Max wrote these patches, so every cord in them is valid: anything flagged is a
false positive. This is the evidence the "raise by default" decision rests on.

Two views of each cord in a ``box``-namespace patcher:

* ``loaded``: as ``Patcher.from_file`` sees it, with the port counts Max wrote.
* ``text``: port counts from box text alone, as for a patch built with
  ``add_textbox``. This is the stricter view.

Usage:
    python scripts/scan_cords.py ~/Documents/"Max 9"/Packages
    python scripts/scan_cords.py DIR --examples 3
"""

from __future__ import annotations

import argparse
import collections
import logging
import sys
from pathlib import Path
from typing import Any, Counter, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from py2max import Patcher  # noqa: E402
from py2max.maxref import message_error, porttypes  # noqa: E402
from py2max.utils import object_name  # noqa: E402


def text_counts(box: Any) -> Tuple[Any, Any]:
    """Port counts from content or text, ignoring the counts Max wrote."""
    sub = porttypes.subpatcher_counts(box)
    if sub != (None, None):
        return sub
    if box.maxclass in porttypes.DYNAMIC_IO_MAXCLASSES:
        return (None, None)
    return porttypes.port_counts(object_name(box), getattr(box, "text", None))


def text_error(p: Any, src: Any, outlet: int, dst: Any, inlet: int) -> str:
    _, n_out = text_counts(src)
    n_in, _ = text_counts(dst)
    if n_out is not None and outlet >= n_out:
        return f"outlet range: {object_name(src)}"
    if n_in is not None and inlet >= n_in:
        return f"inlet range: {object_name(dst)}"
    if {src.maxclass, dst.maxclass} & porttypes.DYNAMIC_IO_MAXCLASSES:
        return ""
    sn, dn = object_name(src), object_name(dst)
    return (
        f"type: {sn}[{outlet}] -> {dn}[{inlet}]"
        if message_error(sn, outlet, dn, inlet)
        else ""
    )


def scan(root: Path) -> Dict[str, Any]:
    counts = {"patches": 0, "unreadable": 0, "cords": 0}
    flags: Dict[str, Counter[str]] = {"loaded": Counter(), "text": Counter()}
    where: Dict[str, List[str]] = collections.defaultdict(list)

    def walk(p: Any, path: Path) -> None:
        if getattr(p, "classnamespace", "box") == "box":
            for line in p._lines:
                (s, so), (d, di) = line.source[:2], line.destination[:2]
                src, dst = p._objects.get(s), p._objects.get(d)
                if src is None or dst is None:
                    continue
                counts["cords"] += 1
                if p._connection_error(s, so, d, di):
                    key = f"{object_name(src)}[{so}] -> {object_name(dst)}[{di}]"
                    flags["loaded"][key] += 1
                    where[key].append(str(path))
                key = text_error(p, src, so, dst, di)
                if key:
                    flags["text"][key] += 1
                    where[key].append(str(path))
        for box in p._boxes:
            if getattr(box, "_patcher", None) is not None:
                walk(box._patcher, path)

    for path in sorted(root.rglob("*")):
        if path.suffix not in (".maxpat", ".maxhelp"):
            continue
        try:
            p = Patcher.from_file(path)
        except Exception:  # noqa: BLE001 - one bad file must not stop the scan
            counts["unreadable"] += 1
            continue
        counts["patches"] += 1
        walk(p, path)
    return {"counts": counts, "flags": flags, "where": where}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("root", type=Path, help="folder of .maxpat/.maxhelp files")
    parser.add_argument("--examples", type=int, default=1, help="paths per class")
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)  # flagged cords are counted, not logged

    result = scan(args.root.expanduser())
    c = result["counts"]
    print(f"{c['patches']} patches ({c['unreadable']} unreadable), {c['cords']} cords")
    for view, flagged in result["flags"].items():
        print(f"\n{view}: {sum(flagged.values())} flagged, {len(flagged)} classes")
        for key, n in flagged.most_common():
            print(f"  {n:5}  {key}")
            for path in result["where"][key][: args.examples]:
                print(f"         {path}")
    sys.exit(1 if any(result["flags"].values()) else 0)


if __name__ == "__main__":
    main()
