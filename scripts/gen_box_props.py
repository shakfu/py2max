#!/usr/bin/env python3
"""Generate ``py2max/core/props.py`` -- the typed Max box-property vocabulary.

Box properties reach the emitted ``.maxpat`` through ``**kwds``, which was typed
``Any``: a misspelled or wrongly-typed property passed every check (including
``mypy --strict``, because ``Any`` is strict-legal) and was written straight into
the patch file. This script generates a ``TypedDict`` describing that vocabulary
so the type checker can reject both.

Usage:
    python scripts/gen_box_props.py            # write py2max/core/props.py
    python scripts/gen_box_props.py --check    # fail if the file is stale

Where the vocabulary comes from
-------------------------------
Three sources, in order of precedence:

1. **Curated types** for the properties users pass most often (colors, fonts,
   presentation, container payloads). Hand-written because precision matters
   most here and because several have no usable maxref type.
2. **maxref attributes whose nested ``save`` meta-attribute is 1** -- exactly the
   attributes Max persists into a patch file, which is what may legitimately
   appear on a box. Their ``type`` and ``size`` give the annotation: ``size`` > 1
   means a sequence.
3. **Keyword names py2max itself passes to ``Box(...)``**, which are correct by
   construction. maxref's attribute lists have gaps -- ``bpatcher`` documents 12
   attributes but not ``viewvisibility``, which py2max writes and Max accepts --
   so the library's own usage is authoritative where the reference is silent.
4. **Keys observed in the ``.maxpat`` fixtures** under ``tests/`` that none of the
   above covers, so round-tripping a real patch never trips the checker.

Two TypedDicts are emitted, differing only in which names they omit:

* ``BoxProps`` for ``Box.__init__``, which declares only the five structural
  parameters, so ``text`` and ``outlettype`` belong in the vocabulary.
* ``TextboxProps`` for the factory entry points, which take ``text``,
  ``outlettype``, ``comment`` and friends as real parameters.

The split is forced: a ``TypedDict`` key colliding with a named parameter makes
mypy report "Overlap between argument names and ** TypedDict items" *and
silently stop checking calls to that function*, which would quietly defeat the
whole exercise. A narrower TypedDict flows into a wider one, so the factory
methods can still forward ``**kwds`` into ``Box``.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "py2max" / "core" / "props.py"

# Functions accepting ``Unpack[BoxProps]``: only ``Box.__init__``, which declares
# just the structural parameters.
BOX_FUNCTIONS = [("py2max/core/box.py", "Box", "__init__")]

# Functions accepting ``Unpack[TextboxProps]``: the factory entry points, which
# take text/outlettype/comment as real parameters and so must omit them.
TEXTBOX_FUNCTIONS = [
    ("py2max/core/factory.py", "BoxFactoryMixin", "add_textbox"),
    ("py2max/core/factory.py", "BoxFactoryMixin", "add_message"),
    ("py2max/core/factory.py", "BoxFactoryMixin", "add_comment"),
    ("py2max/core/factory.py", "BoxFactoryMixin", "add"),
    ("py2max/core/factory.py", "BoxFactoryMixin", "_add_str"),
    ("py2max/core/factory.py", "BoxFactoryMixin", "_add_int"),
    ("py2max/core/factory.py", "BoxFactoryMixin", "_add_float"),
]

# Plumbing that is never a box property.
EXTRA_EXCLUSIONS = {"args", "kwds", "self"}

# Curated annotations for the properties users actually pass. `Sequence` rather
# than `List` so tuples are accepted too.
CURATED: Dict[str, str] = {
    # color: Max writes [r, g, b, a] floats
    "accentcolor": "Sequence[float]",
    "bgcolor": "Sequence[float]",
    "bgfillcolor": "Sequence[float]",
    "bordercolor": "Sequence[float]",
    "color": "Sequence[float]",
    "elementcolor": "Sequence[float]",
    "textcolor": "Sequence[float]",
    "htextcolor": "Sequence[float]",
    "textjustification": "int",
    # geometry
    "presentation_rect": "Sequence[float]",
    "editor_rect": "Sequence[float]",
    # text and font
    "fontname": "str",
    "fontsize": "float",
    "fontface": "int",
    "linecount": "int",
    "format": "int",
    # identity and presentation
    "varname": "str",
    "prototypename": "str",
    "annotation": "str",
    "annotation_name": "str",
    "hint": "str",
    "style": "str",
    "presentation": "int",
    "hidden": "int",
    "ignoreclick": "int",
    "border": "int",
    "rounded": "float",
    "background": "int",
    # values and ranges
    "minimum": "Atom",
    "maximum": "Atom",
    "size": "float",
    "range": "Sequence[Atom]",
    "domain": "float",
    "outputmode": "int",
    "orientation": "int",
    "index": "int",
    "parameter_enable": "int",
    # container payloads and pattr plumbing
    "code": "str",
    "data": "Any",
    "table_data": "Sequence[float]",
    "preset_data": "Sequence[Any]",
    "addpoints": "Sequence[Any]",
    "embed": "int",
    "name": "str",
    "showeditor": "int",
    "saved_attribute_attributes": "Dict[str, Any]",
    "saved_object_attributes": "Dict[str, Any]",
    "lastchannelcount": "int",
    # misc observed in real patches
    "bubble": "int",
    "tabs": "Sequence[str]",
    "items": "Sequence[Any]",
    # written by py2max itself for the rnbo class namespace (see
    # BoxFactoryMixin._textbox_helper); not in maxref, but they reach the file.
    "rnbo_classname": "str",
    "rnbo_extra_attributes": "Dict[str, Any]",
}

# maxref ``type`` -> python annotation for a scalar (``size`` == 1).
SCALAR_TYPES: Dict[str, str] = {
    "int": "int",
    "int32": "int",
    "atom_long": "int",
    "long": "int",
    "float": "float",
    "float64": "float",
    "double": "float",
    "symbol": "str",
    "atom": "Atom",
    "Time Value": "TimeValue",
    "list": "Sequence[Atom]",
    "object": "Any",
}


def parameter_names(functions: List[Tuple[str, str, str]]) -> Set[str]:
    """Names taken as explicit parameters by the given functions."""
    names: Set[str] = set(EXTRA_EXCLUSIONS)
    for rel, cls, func in functions:
        tree = ast.parse((ROOT / rel).read_text())
        for node in ast.walk(tree):
            if not (isinstance(node, ast.ClassDef) and node.name == cls):
                continue
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == func:
                    for arg in item.args.args + item.args.kwonlyargs:
                        names.add(arg.arg)
    return names


def keywords_passed_to_box() -> Set[str]:
    """Keyword names py2max itself passes to ``Box(...)``.

    Correct by construction, and the only source that covers properties maxref
    fails to document (``viewvisibility`` on ``bpatcher``, for one).
    """
    names: Set[str] = set()
    for rel in ("py2max/core/factory.py", "py2max/core/patcher.py"):
        tree = ast.parse((ROOT / rel).read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name) and func.id == "Box":
                for kw in node.keywords:
                    if kw.arg:
                        names.add(kw.arg)
    return names


def fixture_keys() -> Set[str]:
    """Every box key present in the repository's ``.maxpat`` fixtures."""
    keys: Set[str] = set()

    def walk(patcher: dict) -> None:
        for entry in patcher.get("boxes", []):
            box = entry.get("box", {})
            keys.update(box.keys())
            if "patcher" in box:
                walk(box["patcher"])

    for path in sorted((ROOT / "tests").rglob("*.maxpat")):
        with open(path, encoding="utf8") as f:
            walk(json.load(f)["patcher"])
    return keys


def maxref_saved_attributes() -> Tuple[Dict[str, str], Dict[str, Set[str]]]:
    """Attributes Max persists into a patch file, with an annotation for each.

    Returns ``(annotations, objects_by_attribute)``. An attribute whose type
    differs across objects gets a union of the alternatives, so a property that
    is an int on one object and a symbol on another still checks on both.
    """
    sys.path.insert(0, str(ROOT))
    from py2max.maxref import get_available_objects, get_object_info

    candidates: Dict[str, Set[str]] = {}
    owners: Dict[str, Set[str]] = {}
    for name in get_available_objects():
        info = get_object_info(name) or {}
        for attr, spec in (info.get("attributes") or {}).items():
            meta = spec.get("attributes") or {}
            save = (meta.get("save") or {}).get("value")
            if save != "1":
                continue
            scalar = SCALAR_TYPES.get(str(spec.get("type") or ""), "Atom")
            try:
                size = int(str(spec.get("size") or "1"))
            except ValueError:
                size = 1
            annotation = scalar if size == 1 else f"Sequence[{scalar}]"
            candidates.setdefault(attr, set()).add(annotation)
            owners.setdefault(attr, set()).add(name)

    annotations: Dict[str, str] = {}
    for attr, variants in candidates.items():
        if len(variants) == 1:
            annotations[attr] = next(iter(variants))
        else:
            # Widen rather than pick: the same key means different things on
            # different objects, and rejecting either would be wrong.
            annotations[attr] = f"Union[{', '.join(sorted(variants))}]"
    return annotations, owners


def is_identifier_key(name: str) -> bool:
    """TypedDict keys generated as class attributes must be valid identifiers."""
    return name.isidentifier()


def build() -> str:
    from_maxref, _owners = maxref_saved_attributes()
    fixtures = fixture_keys()
    from_library = keywords_passed_to_box()

    entries: Dict[str, str] = {}
    provenance: Dict[str, str] = {}

    for name, annotation in sorted(from_maxref.items()):
        entries[name] = annotation
        provenance[name] = "maxref"
    # py2max's own usage outranks maxref: where the reference is silent or wrong,
    # what the library writes is what ends up in the file.
    for name in sorted(from_library):
        if name not in entries:
            entries[name] = CURATED.get(name, "Any")
            provenance[name] = "library"
    for name, annotation in sorted(CURATED.items()):
        entries[name] = annotation
        provenance[name] = "curated"
    # Fixture keys nothing else covered: permissive, but present, so a real patch
    # never fails the checker on a key Max itself wrote.
    for name in sorted(k for k in fixtures if k not in entries):
        entries[name] = "Any"
        provenance[name] = "fixture"

    for name in list(entries):
        if not is_identifier_key(name):
            del entries[name]

    box_excluded = parameter_names(BOX_FUNCTIONS)
    textbox_excluded = box_excluded | parameter_names(TEXTBOX_FUNCTIONS)

    box_entries = {k: v for k, v in entries.items() if k not in box_excluded}
    textbox_entries = {k: v for k, v in entries.items() if k not in textbox_excluded}

    counts = {
        source: sum(1 for k, s in provenance.items() if s == source and k in box_entries)
        for source in ("curated", "maxref", "library", "fixture")
    }

    lines: List[str] = []
    lines.append('"""Typed Max box properties.')
    lines.append("")
    lines.append("GENERATED FILE -- DO NOT EDIT BY HAND.")
    lines.append("Regenerate with: python scripts/gen_box_props.py")
    lines.append("")
    lines.append(
        "``BoxProps`` describes the keyword properties a Max box may carry, so that\n"
        "``**kwds`` on the box-creating api can be typed instead of ``Any``. A\n"
        "misspelled property name or a wrongly-typed value is then a type error\n"
        "rather than a key silently written into the emitted ``.maxpat``."
    )
    lines.append("")
    lines.append(
        f"Vocabulary: {counts['curated']} curated + {counts['maxref']} from maxref\n"
        f"(attributes whose ``save`` meta-attribute is 1, i.e. the ones Max persists\n"
        f"into a patch) + {counts['library']} from py2max's own ``Box(...)`` calls\n"
        f"+ {counts['fixture']} seen only in the repository's .maxpat fixtures\n"
        f"= {len(box_entries)} properties."
    )
    lines.append("")
    lines.append(
        "``total=False`` throughout: every property is optional, which is what Max's\n"
        "format means -- an absent key and a key set to null are different things."
    )
    lines.append("")
    lines.append(
        "Two dicts, differing only in which names they omit. A TypedDict key that\n"
        "collides with a named parameter makes mypy report an overlap error *and stop\n"
        "checking calls to that function*, so each is trimmed to its call sites:\n"
        "``BoxProps`` for ``Box.__init__`` (five structural parameters, so ``text`` and\n"
        "``outlettype`` stay in), ``TextboxProps`` for the factory entry points, which\n"
        "take those as real parameters. The narrower flows into the wider, so the\n"
        "factory can forward ``**kwds`` straight into ``Box``."
    )
    lines.append('"""')
    lines.append("")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from typing import Any, Dict, Sequence, TypedDict, Union")
    lines.append("")
    lines.append("#: A Max atom: the loosest useful value type.")
    lines.append("Atom = Union[str, int, float]")
    lines.append("")
    lines.append('#: A Max time value: milliseconds, or notation such as "4n".')
    lines.append("TimeValue = Union[int, float, str]")
    lines.append("")
    lines.append("")
    lines.append("class BoxProps(TypedDict, total=False):")
    lines.append('    """Properties accepted by ``Box.__init__`` beyond its structural args."""')
    lines.append("")
    for name in sorted(box_entries):
        lines.append(f"    {name}: {box_entries[name]}")
    lines.append("")
    lines.append("")
    lines.append("class TextboxProps(TypedDict, total=False):")
    lines.append(
        '    """As :class:`BoxProps`, minus the names the factory takes as parameters."""'
    )
    lines.append("")
    for name in sorted(textbox_entries):
        lines.append(f"    {name}: {textbox_entries[name]}")
    lines.append("")
    lines.append("")
    lines.append("#: Every property name in :class:`BoxProps`, for runtime checks.")
    lines.append("BOX_PROP_NAMES = frozenset(BoxProps.__annotations__)")
    lines.append("")
    return "\n".join(lines)


def postprocess(path: Path) -> None:
    for cmd in (["ruff", "format", str(path)], ["ruff", "check", "--fix", "--quiet", str(path)]):
        subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    ast.parse(path.read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true", help="fail if the file is stale")
    args = parser.parse_args()

    source = build()
    if args.check:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "props.py"
            tmp.write_text(source)
            postprocess(tmp)
            fresh = tmp.read_text()
        current: Optional[str] = args.output.read_text() if args.output.exists() else None
        if fresh != current:
            print(f"{args.output} is stale; run: python scripts/gen_box_props.py")
            return 1
        print(f"{args.output} is up to date")
        return 0

    args.output.write_text(source)
    postprocess(args.output)
    count = len(
        [
            line
            for line in args.output.read_text().splitlines()
            if line.startswith("    ") and ": " in line and not line.startswith("    \"")
        ]
    )
    print(f"wrote {args.output} ({count} properties)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
