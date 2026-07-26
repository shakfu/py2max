#!/usr/bin/env python3
"""Generate ``js2max/src/objects.ts`` -- the box facts js2max cannot ask Max for.

Serializing a live patcher needs three things per box that the Max JS API does
not expose. A probe run inside Max established exactly which:

    getboxattr("maxclass")   -> null      the *box* class is not a box attribute
    getboxattr("numinlets")  -> null      nor are the port counts
    getboxattr("numoutlets") -> null
    Maxobj.maxclass          -> "print"   the *object* class, which is a key
    Maxobj.boxtext           -> "print x" the typed-in text, which is enough

So the object class is available and the rest is static per class -- which is
precisely what py2max already knows from the maxref bundle. This exports it.

Two tables come out:

* ``OWN_MAXCLASS`` -- classes whose box keeps its own ``maxclass`` in the file.
  Everything else is an object box, written as ``maxclass: "newobj"`` with the
  class name inside ``text``.
* ``PORTS`` -- ``numinlets`` / ``numoutlets`` / ``outlettype`` per class.

Usage:
    python scripts/gen_js2max_objects.py            # write the table
    python scripts/gen_js2max_objects.py --check    # fail if it is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from py2max import Patcher, maxref  # noqa: E402
from py2max.core.patcher import (  # noqa: E402
    MAX_VER_MAJOR,
    MAX_VER_MINOR,
    MAX_VER_REVISION,
)

DEFAULT_OUT = ROOT / "js2max" / "src" / "objects.ts"

# Classes py2max builds with a dedicated method rather than `add_textbox`.
#
# Probing `add_textbox` alone gets these wrong: `add_textbox("comment")` reports
# 1 inlet / 1 outlet, while a real comment box -- what `add_comment` writes -- is
# 0 in / 1 out. The dedicated method is the authority, so call it.
FACTORY_ADDERS = {
    "comment": lambda p: p.add_comment("x"),
    "message": lambda p: p.add_message("x"),
    "umenu": lambda p: p.add_umenu(),
    "bpatcher": lambda p: p.add_bpatcher(name="x"),
    "flonum": lambda p: p.add_floatbox(),
    "number": lambda p: p.add_intbox(),
    "itable": lambda p: p.add_itable(name="x"),
    "gen.codebox~": lambda p: p.add_gen_codebox("out1 = in1;"),
}

# Set directly by the factory but without a probe-able adder of its own.
EXTRA_MAXCLASSES = {"attrui"}


def collect() -> Tuple[Set[str], Dict[str, Tuple[int, int, Optional[List[str]]]]]:
    """Ask py2max what it would emit for every known object."""
    patcher = Patcher(str(ROOT / "build" / "_gen.maxpat"))
    own: Set[str] = set(EXTRA_MAXCLASSES) | set(FACTORY_ADDERS)
    ports: Dict[str, Tuple[int, int, Optional[List[str]]]] = {}

    names = sorted(set(maxref.get_available_objects()) | set(FACTORY_ADDERS))
    for name in names:
        adder = FACTORY_ADDERS.get(name)
        try:
            box = adder(patcher) if adder else patcher.add_textbox(name)
        except Exception:  # noqa: BLE001 - a bad entry must not stop the export
            continue
        box_dict: Dict[str, Any] = box.to_dict()["box"]

        maxclass = box_dict.get("maxclass", "newobj")
        if maxclass != "newobj":
            own.add(name)

        if adder is not None:
            # A dedicated adder encodes real knowledge, so trust its box.
            numinlets = box_dict.get("numinlets")
            numoutlets = box_dict.get("numoutlets")
            outlettype = box_dict.get("outlettype")
        else:
            # Otherwise read maxref directly rather than the constructed box:
            # `Box.__init__` defaults numoutlets to 1, and for the 73 objects
            # maxref does not state it that default is simply wrong -- `print`
            # came out with an outlet it does not have. An absent count is
            # omitted from the table, and Max derives it from the object.
            defaults = maxref.MAXCLASS_DEFAULTS.get(name) or {}
            numinlets = defaults.get("numinlets")
            numoutlets = defaults.get("numoutlets")
            outlettype = defaults.get("outlettype")

        if numinlets is None or numoutlets is None:
            continue
        ports[name] = (
            int(numinlets),
            int(numoutlets),
            list(outlettype) if outlettype else None,
        )

    return own, ports


def render(own: Set[str], ports: Dict[str, Tuple[int, int, Optional[List[str]]]]) -> str:
    """Emit the table compactly: one line per class, values positional."""
    lines: List[str] = []
    lines.append("/**")
    lines.append(" * Box facts the Max JS API does not expose, exported from py2max.")
    lines.append(" *")
    lines.append(" * GENERATED FILE -- DO NOT EDIT BY HAND.")
    lines.append(" * Regenerate with: python scripts/gen_js2max_objects.py")
    lines.append(" *")
    lines.append(" * A probe run inside Max established that `getboxattr` returns null for")
    lines.append(" * `maxclass`, `numinlets` and `numoutlets` -- they are not box attributes.")
    lines.append(" * What *is* available is `Maxobj.maxclass` (the object class) and")
    lines.append(" * `Maxobj.boxtext`. The object class is the key into these tables, which")
    lines.append(" * supply the rest.")
    lines.append(" *")
    lines.append(f" * {len(own)} classes keep their own `maxclass`; {len(ports)} have port counts.")
    lines.append(" */")
    lines.append("")
    lines.append("/** Classes whose box keeps its own `maxclass`; everything else is `newobj`. */")
    lines.append("export const OWN_MAXCLASS: ReadonlySet<string> = new Set([")
    for name in sorted(own):
        lines.append(f"  {json.dumps(name)},")
    lines.append("]);")
    lines.append("")
    lines.append("/** `[numinlets, numoutlets, outlettype?]`, keyed by object class. */")
    lines.append("export type PortEntry =")
    lines.append("  | readonly [number, number]")
    lines.append("  | readonly [number, number, readonly string[]];")
    lines.append("")
    lines.append("export const PORTS: Readonly<Record<string, PortEntry>> = {")
    for name in sorted(ports):
        numinlets, numoutlets, outlettype = ports[name]
        value = f"[{numinlets}, {numoutlets}"
        if outlettype:
            value += ", " + json.dumps(outlettype).replace('", "', '", "')
        value += "]"
        lines.append(f"  {json.dumps(name)}: {value},")
    lines.append("};")
    lines.append("")
    lines.append("/** The `maxclass` a box of this object class carries in the file. */")
    lines.append("export function boxClassOf(objectClass: string): string {")
    lines.append('  return OWN_MAXCLASS.has(objectClass) ? objectClass : "newobj";')
    lines.append("}")
    lines.append("")
    lines.append("/**")
    lines.append(" * The Max version a written file declares, taken from py2max.")
    lines.append(" *")
    lines.append(" * Exported rather than restated so the two packages cannot claim to")
    lines.append(" * have been written by different versions of Max. It was a literal in")
    lines.append(" * `model.ts`, which would have gone quietly stale the first time")
    lines.append(" * py2max bumped `MAX_VER_*` in `core/patcher.py`.")
    lines.append(" */")
    lines.append("export const APP_VERSION = {")
    lines.append(f"  major: {MAX_VER_MAJOR},")
    lines.append(f"  minor: {MAX_VER_MINOR},")
    lines.append(f"  revision: {MAX_VER_REVISION},")
    lines.append('  architecture: "x64",')
    lines.append("  modernui: 1,")
    lines.append("} as const;")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true", help="fail if stale")
    args = parser.parse_args()

    (ROOT / "build").mkdir(exist_ok=True)
    own, ports = collect()
    fresh = render(own, ports)

    if args.check:
        current = args.output.read_text() if args.output.exists() else None
        if current != fresh:
            print(f"{args.output} is stale; run: python scripts/gen_js2max_objects.py")
            return 1
        print(f"{args.output} is up to date")
        return 0

    args.output.write_text(fresh)
    print(
        f"wrote {args.output} ({len(own)} own-maxclass, {len(ports)} port entries,"
        f" {len(fresh) // 1024} KB)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
