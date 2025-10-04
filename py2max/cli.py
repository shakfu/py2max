"""Command line interface for the py2max package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from pprint import pprint
from textwrap import fill
from typing import Iterable, List, Dict, Any, cast

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

from .core import InvalidConnectionError, Patcher, Patchline
from .common import Rect
from .maxref import MaxRefCache, validate_connection
from .transformers import available_transformers, create_transformer, run_pipeline
from .converters import maxpat_to_python, maxref_to_sqlite


LAYOUT_CHOICES = ["horizontal", "vertical", "grid", "flow", "matrix"]
FLOW_CHOICES = ["horizontal", "vertical", "column"]


def _sanitize_identifier(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in name)
    cleaned = cleaned.strip("_") or "identifier"
    if cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    return cleaned


def _to_pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in _sanitize_identifier(name).split("_")) or "Object"


def _object_name(box) -> str:
    maxclass = getattr(box, "maxclass", "newobj")
    text = getattr(box, "text", "") or ""
    if maxclass == "newobj" and text:
        return text.split()[0]
    return maxclass


def _unique_object_labels(boxes: Iterable) -> List[str]:
    labels: set[str] = set()
    for box in boxes:
        labels.add(_object_name(box))
    return sorted(labels)


def _coerce_rect(patcher: Patcher) -> None:
    rect = getattr(patcher, "rect", None)
    if isinstance(rect, (list, tuple)) and len(rect) == 4:
        patcher.rect = Rect(*rect)


def _format_args(method: dict) -> List[str]:
    args: List[str] = []
    for arg in method.get("args", []):
        name = _sanitize_identifier(arg.get("name", "arg"))
        optional = str(arg.get("optional", "0")) == "1"
        if optional:
            args.append(f"{name}=None")
        else:
            args.append(name)
    return args


def _dump_code(name: str, data: dict) -> None:
    class_name = _to_pascal_case(name)
    digest = data.get("digest", "")
    description = data.get("description", "")

    print(f"class {class_name}:")
    print("    \"\"\"" + digest)
    if description:
        formatted = fill(description, width=76, initial_indent="    ", subsequent_indent="    ")
        for line in formatted.splitlines():
            print(line)
    print("    \"\"\"")

    for method_name, method in sorted(data.get("methods", {}).items()):
        if method_name.startswith("("):
            continue
        identifier = _sanitize_identifier(method_name)
        signature = ", ".join(["self"] + _format_args(method))
        print(f"    def {identifier}({signature}):")
        digest = method.get("digest")
        if digest:
            print(f"        \"\"\"{digest}\"\"\"")
        description = method.get("description")
        if description and description != "TEXT_HERE":
            formatted = fill(description, width=70, initial_indent="        ", subsequent_indent="        ")
            for line in formatted.splitlines():
                print(line)
        print("        raise NotImplementedError\n")


def _dump_tests(name: str, data: dict) -> None:
    base = _sanitize_identifier(name)
    for method_name, method in sorted(data.get("methods", {}).items()):
        identifier = _sanitize_identifier(method_name)
        digest = method.get("digest", "")
        print(f"def test_{base}_{identifier}():")
        if digest:
            print(f"    \"\"\"{digest}\"\"\"")
        print("    # TODO: implement test\n")


def _generate_test_source(name: str, data: dict) -> str:
    base = _sanitize_identifier(name)
    lines = [
        "from py2max.maxref import MaxRefCache",
        "",
        f"def test_{base}_maxref():",
        "    cache = MaxRefCache()",
        f"    data = cache.get_object_data(\"{name}\")",
        "    assert data is not None",
    ]

    digest = data.get("digest")
    if digest:
        lines.append(f"    assert data.get(\"digest\") == {digest!r}")

    inlet_count = len(data.get("inlets", []) or [])
    if inlet_count:
        lines.append(f"    assert len(data.get(\"inlets\", [])) == {inlet_count}")

    outlet_count = len(data.get("outlets", []) or [])
    if outlet_count:
        lines.append(f"    assert len(data.get(\"outlets\", [])) == {outlet_count}")

    return "\n".join(lines) + "\n"


def cmd_new(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if path.exists() and not args.force:
        print(f"Refusing to overwrite existing file: {path}", file=sys.stderr)
        return 1

    patcher = Patcher(
        path=path,
        title=args.title,
        layout=args.layout,
        flow_direction=args.flow_direction,
    )

    if args.template == "stereo":
        osc = patcher.add("cycle~ 440")
        gain = patcher.add("gain~")
        dac = patcher.add("ezdac~")
        patcher.link(osc, gain)
        patcher.link(gain, dac)
        patcher.link(gain, dac, inlet=1)
    elif args.template == "blank":
        pass
    else:
        print(f"Unknown template: {args.template}", file=sys.stderr)
        return 2

    patcher.save()
    print(f"Created patcher at {path}")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    path = Path(args.path)
    patcher = Patcher.from_file(path)
    _coerce_rect(patcher)
    boxes = patcher._boxes
    lines = patcher._lines

    print(f"Path: {path}")
    print(f"Boxes: {len(boxes)}")
    print(f"Patchlines: {len(lines)}")
    labels = _unique_object_labels(boxes)
    print("Objects: " + (", ".join(labels) if labels else "(none)"))

    if args.verbose:
        for box in boxes:
            identifier = getattr(box, "id", "(unknown)")
            obj_label = getattr(box, "text", None) or getattr(box, "maxclass", "newobj")
            print(f"  - {identifier}: {obj_label}")

    return 0


def cmd_optimize(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    save_path = Path(args.output) if args.output else input_path

    patcher = Patcher.from_file(input_path, save_to=str(save_path))
    _coerce_rect(patcher)

    if args.flow_direction:
        patcher._flow_direction = args.flow_direction
        if hasattr(patcher._layout_mgr, "flow_direction"):
            patcher._layout_mgr.flow_direction = args.flow_direction

    if args.layout:
        patcher._layout_mgr = patcher.set_layout_mgr(args.layout)

    patcher.optimize_layout()
    patcher.save_as(save_path)
    print(f"Optimized layout saved to {save_path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    patcher = Patcher.from_file(path)
    _coerce_rect(patcher)

    errors: List[str] = []

    for line in patcher._lines:
        patchline = cast(Patchline, line)
        src_id, dst_id = patchline.src, patchline.dst
        src_port = int(patchline.source[1]) if len(patchline.source) > 1 else 0
        dst_port = int(patchline.destination[1]) if len(patchline.destination) > 1 else 0

        src_obj = patcher._objects.get(src_id)
        dst_obj = patcher._objects.get(dst_id)

        if not src_obj or not dst_obj:
            errors.append(f"Dangling connection: {src_id} -> {dst_id}")
            continue

        src_name = _object_name(src_obj)
        dst_name = _object_name(dst_obj)

        is_valid, message = validate_connection(src_name, src_port, dst_name, dst_port)
        if not is_valid:
            errors.append(
                f"Invalid connection {src_name}[{src_port}] -> {dst_name}[{dst_port}]: {message}"
            )

    if errors:
        print("Connection validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("All connections are valid.")
    return 0


def _parse_transform_spec(spec: str) -> tuple[str, str | None]:
    if "=" in spec:
        name, value = spec.split("=", 1)
        name = name.strip()
        value = value.strip()
        return name, value or None
    return spec.strip(), None


def cmd_transform(args: argparse.Namespace) -> int:
    if args.list_transformers:
        for name, desc in available_transformers().items():
            print(f"{name}: {desc}")
        return 0

    if not args.input:
        print("Please provide an input .maxpat file.", file=sys.stderr)
        return 1

    if not args.apply:
        print("No transformers specified. Use --apply name or --apply name=value.", file=sys.stderr)
        return 1

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path

    patcher = Patcher.from_file(input_path, save_to=str(output_path))

    transformers = []
    for spec in args.apply:
        name, value = _parse_transform_spec(spec)
        try:
            transformer = create_transformer(name, value)
        except KeyError:
            print(f"Unknown transformer '{name}'. Use --list-transformers to see options.", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        transformers.append(transformer)

    run_pipeline(patcher, transformers)
    patcher.save_as(output_path)
    print(f"Saved transformed patcher to {output_path}")
    return 0


def cmd_convert(args: argparse.Namespace) -> int:
    if args.mode == "maxpat-to-python":
        if not args.input or not args.output:
            print(
                "Usage: py2max convert maxpat-to-python <input.maxpat> <output.py>",
                file=sys.stderr,
            )
            return 1

        maxpat_to_python(args.input, args.output, default_output=args.default_output)
        print(f"Wrote Python builder to {args.output}")
        return 0

    if args.mode == "maxref-to-sqlite":
        if not args.output:
            print(
                "Usage: py2max convert maxref-to-sqlite --output cache.db [--names name1 name2]",
                file=sys.stderr,
            )
            return 1

        names = args.names if args.names else None
        count = maxref_to_sqlite(args.output, names=names, overwrite=args.overwrite)
        print(f"Stored {count} maxref entr{'y' if count == 1 else 'ies'} in {args.output}")
        return 0

    print(
        "Unknown convert mode. Supported: maxpat-to-python, maxref-to-sqlite",
        file=sys.stderr,
    )
    return 1


def cmd_maxref(args: argparse.Namespace) -> int:
    cache = MaxRefCache()

    if args.list:
        names = sorted(cache.refdict.keys())
        for name in names:
            print(name)
        return 0

    if args.info:
        names = sorted(cache.refdict.keys())
        for name in names:
            info = cache.get_object_data(name) or {}
            digest = info.get("digest", "")
            print(f"{name}: {digest}")
        return 0

    if not args.name:
        print("Please specify a Max object name (e.g. 'cycle~').", file=sys.stderr)
        return 1

    data_dict = cache.get_object_data(args.name)
    if not data_dict:
        print(f"Could not load maxref for '{args.name}'.", file=sys.stderr)
        return 1
    data: Dict[str, Any] = data_dict

    if args.dict:
        pprint(data)
        return 0

    if args.code:
        _dump_code(args.name, data)
        return 0

    if args.json:
        print(json.dumps(data, indent=2))
        return 0

    if args.test:
        if args.output:
            output_path = Path(args.output)
            if output_path.parent:
                output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(_generate_test_source(args.name, data), encoding="utf8")
            print(f"Wrote test skeleton to {output_path}")
        else:
            _dump_tests(args.name, data)
        return 0

    if args.yaml:
        if yaml is None:
            print("PyYAML is not installed; cannot emit YAML output.", file=sys.stderr)
            return 1
        print(yaml.safe_dump(data))
        return 0

    digest = data.get("digest", "")
    description = data.get("description", "")
    print(f"{args.name}")
    if digest:
        print(f"  Digest: {digest}")
    if description:
        print("  Description:")
        formatted = fill(description, width=76, initial_indent="    ", subsequent_indent="    ")
        for line in formatted.splitlines():
            print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="py2max", description="Utilities for working with Max patchers.")
    subparsers = parser.add_subparsers(dest="command")

    new_parser = subparsers.add_parser("new", help="Create a new patcher file")
    new_parser.add_argument("path", help="Destination .maxpat path")
    new_parser.add_argument("--title", help="Optional patcher title")
    new_parser.add_argument("--layout", choices=LAYOUT_CHOICES, default="horizontal")
    new_parser.add_argument("--flow-direction", choices=FLOW_CHOICES, default="horizontal")
    new_parser.add_argument(
        "--template",
        choices=["blank", "stereo"],
        default="blank",
        help="Preset object layout to populate the patch",
    )
    new_parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    new_parser.set_defaults(func=cmd_new)

    info_parser = subparsers.add_parser("info", help="Summarize an existing patcher")
    info_parser.add_argument("path", help="Target .maxpat path")
    info_parser.add_argument("--verbose", action="store_true", help="List every object in the patch")
    info_parser.set_defaults(func=cmd_info)

    opt_parser = subparsers.add_parser("optimize", help="Run layout optimization on a patch")
    opt_parser.add_argument("input", help="Existing .maxpat file")
    opt_parser.add_argument("-o", "--output", help="Output path (defaults to in-place)")
    opt_parser.add_argument("--layout", choices=LAYOUT_CHOICES, help="Override layout manager before optimizing")
    opt_parser.add_argument("--flow-direction", choices=FLOW_CHOICES, help="Set flow direction before optimizing")
    opt_parser.set_defaults(func=cmd_optimize)

    val_parser = subparsers.add_parser("validate", help="Validate patcher connections against maxref metadata")
    val_parser.add_argument("path", help="Target .maxpat path")
    val_parser.set_defaults(func=cmd_validate)

    transform_parser = subparsers.add_parser("transform", help="Apply transformer pipeline to a patcher")
    transform_parser.add_argument("input", nargs="?", help="Source .maxpat file")
    transform_parser.add_argument("-o", "--output", help="Destination path (defaults to input)")
    transform_parser.add_argument(
        "-t",
        "--apply",
        metavar="NAME[=VALUE]",
        action="append",
        help="Transformer to apply (may be specified multiple times)",
    )
    transform_parser.add_argument(
        "-l",
        "--list-transformers",
        action="store_true",
        dest="list_transformers",
        help="List available transformers and exit",
    )
    transform_parser.set_defaults(func=cmd_transform)

    convert_parser = subparsers.add_parser("convert", help="Convert between patch representations")
    convert_sub = convert_parser.add_subparsers(dest="mode")

    convert_mp_py = convert_sub.add_parser(
        "maxpat-to-python",
        help="Generate a Python script that recreates a .maxpat file",
    )
    convert_mp_py.add_argument("input", help="Source .maxpat file")
    convert_mp_py.add_argument("output", help="Destination Python file")
    convert_mp_py.add_argument(
        "--default-output",
        help="Default output path embedded in the generated script",
    )
    convert_mp_py.set_defaults(func=cmd_convert)

    convert_maxref = convert_sub.add_parser(
        "maxref-to-sqlite",
        help="Cache maxref metadata into an SQLite database",
    )
    convert_maxref.add_argument(
        "--output",
        required=True,
        help="SQLite database path to write",
    )
    convert_maxref.add_argument(
        "--names",
        nargs="*",
        help="Optional list of object names to include (defaults to all)",
    )
    convert_maxref.add_argument(
        "--overwrite",
        action="store_true",
        help="Remove existing database before writing",
    )
    convert_maxref.set_defaults(func=cmd_convert)

    maxref_parser = subparsers.add_parser("maxref", help="Inspect Cycling '74 maxref metadata")
    maxref_parser.add_argument("name", nargs="?", help="Max object name (without .maxref.xml)")
    maxref_parser.add_argument("--dict", action="store_true", help="Dump parsed maxref as a Python dict")
    maxref_parser.add_argument("--json", action="store_true", help="Dump parsed maxref as JSON")
    maxref_parser.add_argument("--code", action="store_true", help="Generate a Python class outline")
    maxref_parser.add_argument("--test", action="store_true", help="Generate pytest skeletons")
    maxref_parser.add_argument("-o", "--output", help="Write generated code/tests to this file")
    maxref_parser.add_argument("--yaml", action="store_true", help="Dump parsed maxref as YAML (requires PyYAML)")
    maxref_parser.add_argument("--list", action="store_true", help="List all available maxref entries")
    maxref_parser.add_argument("--info", action="store_true", help="List all entries with their digests")
    maxref_parser.set_defaults(func=cmd_maxref)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except InvalidConnectionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


__all__ = ["main"]
