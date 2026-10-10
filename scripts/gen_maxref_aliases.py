#!/usr/bin/env python3
"""Generate ``py2max/maxref/aliases.py`` -- typed object name -> maxref key.

maxref keys objects by refpage file name, which is not always the name typed
into a box: ``*~`` lives in ``times~.maxref.xml``, and abbreviations such as
``t``, ``sel`` and ``p`` have no refpage at all. Two sources fill the gap:

1. The ``name`` each bundle entry records (``times~`` -> ``*~``).
2. Max's own ``C74/init/*-objectmappings.txt`` lines,
   ``max objectfile <typed> <file> [<refpage>];``.

Targets are checked against the shipped bundle, so the table does not depend on
the Max version beyond its mapping files. Needs a Max install for source 2.

Usage:
    python scripts/gen_maxref_aliases.py            # write the module
    python scripts/gen_maxref_aliases.py --check    # fail if it is stale
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Set

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "py2max" / "maxref" / "data" / "bundle.json.gz"
OUT = ROOT / "py2max" / "maxref" / "aliases.py"

_MAPPING = re.compile(r"^max objectfile (\S+) (\S+)(?: (\S+))?\s*;", re.MULTILINE)


def find_init_dir() -> Path:
    """Max's ``C74/init`` folder, from ``PY2MAX_MAX_REFPAGES`` or discovery."""
    sys.path.insert(0, str(ROOT))
    from py2max.maxref.parser import MaxRefCache

    refpages = MaxRefCache()._get_refpages()
    if refpages is None:
        sys.exit("no Max install found; set PY2MAX_MAX_REFPAGES")
    init = refpages.parent.parent / "init"  # C74/docs/refpages -> C74/init
    if not init.is_dir():
        sys.exit(f"no init folder at {init}")
    return init


def build(init: Path) -> Dict[str, str]:
    with gzip.open(BUNDLE, "rb") as fh:
        objects = json.loads(fh.read().decode("utf-8"))["objects"]
    keys: Set[str] = set(objects)
    aliases: Dict[str, str] = {}
    for key, entry in objects.items():
        name = entry.get("name")
        if name and name != key and " " not in name and name not in keys:
            aliases[name] = key
    for path in sorted(init.glob("*objectmappings.txt")):
        for typed, file, ref in _MAPPING.findall(path.read_text(errors="replace")):
            if typed in keys or typed in aliases:
                continue
            target = next((t for t in (ref, file) if t in keys), None)
            if target is not None:
                aliases[typed] = target
    return dict(sorted(aliases.items()))


def render(aliases: Dict[str, str]) -> str:
    lines = [
        '"""Typed object name -> maxref key, for names maxref does not file under.',
        "",
        "GENERATED FILE -- DO NOT EDIT BY HAND.",
        "Regenerate with: python scripts/gen_maxref_aliases.py",
        '"""',
        "",
        "from typing import Dict",
        "",
        "ALIASES: Dict[str, str] = {",
    ]
    lines += [f"    {json.dumps(k)}: {json.dumps(v)}," for k, v in aliases.items()]
    lines += ["}", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="fail if stale")
    args = parser.parse_args()
    text = render(build(find_init_dir()))
    if args.check:
        if not OUT.exists() or OUT.read_text() != text:
            sys.exit(f"{OUT} is stale; run: python scripts/gen_maxref_aliases.py")
        return
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    os.environ.setdefault("PY2MAX_LOG_LEVEL", "ERROR")
    main()
