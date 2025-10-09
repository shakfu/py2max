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
from .db import MaxRefDB
from .svg import export_svg


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


def cmd_db(args: argparse.Namespace) -> int:
    """Handle database subcommands"""
    if args.db_command == "create":
        return cmd_db_create(args)
    elif args.db_command == "populate":
        return cmd_db_populate(args)
    elif args.db_command == "info":
        return cmd_db_info(args)
    elif args.db_command == "search":
        return cmd_db_search(args)
    elif args.db_command == "query":
        return cmd_db_query(args)
    elif args.db_command == "export":
        return cmd_db_export(args)
    elif args.db_command == "import":
        return cmd_db_import(args)
    elif args.db_command == "cache":
        return cmd_db_cache(args)
    else:
        print(f"Unknown db subcommand: {args.db_command}", file=sys.stderr)
        return 1


def cmd_db_create(args: argparse.Namespace) -> int:
    """Create a new MaxRefDB database"""
    db_path = Path(args.database)

    if db_path.exists() and not args.force:
        print(f"Database already exists: {db_path}", file=sys.stderr)
        print("Use --force to overwrite or use 'db populate' to add to existing database", file=sys.stderr)
        return 1

    if db_path.exists():
        db_path.unlink()

    db = MaxRefDB(db_path, auto_populate=False)

    if not args.empty:
        # Populate with specified category or all
        category = args.category if hasattr(args, 'category') else None
        print(f"Creating database and populating with {category or 'all'} objects...")
        db.populate(category=category)
        print(f"Created database with {db.count} objects at {db_path}")
    else:
        print(f"Created empty database at {db_path}")

    return 0


def cmd_db_populate(args: argparse.Namespace) -> int:
    """Populate an existing MaxRefDB database"""
    db_path = Path(args.database)

    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        print("Use 'db create' to create a new database", file=sys.stderr)
        return 1

    db = MaxRefDB(db_path, auto_populate=False)
    initial_count = db.count

    if args.objects:
        print(f"Populating with {len(args.objects)} specific objects...")
        db.populate(args.objects)
    elif args.category:
        print(f"Populating with {args.category} objects...")
        db.populate(category=args.category)
    else:
        print("Populating with all objects...")
        db.populate()

    added = db.count - initial_count
    print(f"Added {added} objects (total: {db.count})")
    return 0


def cmd_db_info(args: argparse.Namespace) -> int:
    """Show information about a MaxRefDB database"""
    db_path = Path(args.database)

    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 1

    db = MaxRefDB(db_path, auto_populate=False)

    print(f"Database: {db_path}")
    print(f"Total objects: {db.count}")

    if args.summary:
        summary = db.summary()
        print("\nCategories:")
        for category, count in sorted(summary['categories'].items()):
            print(f"  {category}: {count} objects")

    if args.list:
        print("\nObjects:")
        for obj_name in db.objects:
            print(f"  {obj_name}")

    if args.categories:
        print("\nCategories:")
        for category in db.categories:
            print(f"  {category}")

    return 0


def cmd_db_search(args: argparse.Namespace) -> int:
    """Search for objects in a MaxRefDB database"""
    db_path = Path(args.database)

    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 1

    db = MaxRefDB(db_path, auto_populate=False)

    if args.category:
        results = db.by_category(args.category)
        print(f"Objects in category '{args.category}':")
    else:
        fields = args.fields.split(',') if args.fields else None
        results = db.search(args.query, fields=fields)
        print(f"Search results for '{args.query}':")

    if not results:
        print("  (no matches)")
        return 0

    for name in results:
        if args.verbose:
            obj = db[name]
            digest = obj.get('digest', '')
            print(f"  {name}: {digest}")
        else:
            print(f"  {name}")

    print(f"\nFound {len(results)} objects")
    return 0


def cmd_db_query(args: argparse.Namespace) -> int:
    """Query object details from a MaxRefDB database"""
    db_path = Path(args.database)

    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 1

    db = MaxRefDB(db_path, auto_populate=False)

    if args.name not in db:
        print(f"Object not found: {args.name}", file=sys.stderr)
        return 1

    obj = db[args.name]

    if args.json:
        print(json.dumps(obj, indent=2))
    elif args.dict:
        pprint(obj)
    else:
        # Human-readable output
        print(f"{args.name}")
        if obj.get('digest'):
            print(f"  Digest: {obj['digest']}")
        if obj.get('description'):
            print(f"  Description: {obj['description']}")
        if obj.get('category'):
            print(f"  Category: {obj['category']}")

        inlets = obj.get('inlets', [])
        outlets = obj.get('outlets', [])
        if inlets:
            print(f"  Inlets: {len(inlets)}")
        if outlets:
            print(f"  Outlets: {len(outlets)}")

        methods = obj.get('methods', {})
        attributes = obj.get('attributes', {})
        if methods:
            print(f"  Methods: {len(methods)}")
        if attributes:
            print(f"  Attributes: {len(attributes)}")

    return 0


def cmd_db_export(args: argparse.Namespace) -> int:
    """Export MaxRefDB database to JSON"""
    db_path = Path(args.database)

    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output)

    if output_path.exists() and not args.force:
        print(f"Output file already exists: {output_path}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        return 1

    db = MaxRefDB(db_path, auto_populate=False)
    db.export(output_path)
    print(f"Exported {db.count} objects to {output_path}")
    return 0


def cmd_db_import(args: argparse.Namespace) -> int:
    """Import JSON data into MaxRefDB database"""
    db_path = Path(args.database)
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        print("Use 'db create --empty' to create a new database first", file=sys.stderr)
        return 1

    db = MaxRefDB(db_path, auto_populate=False)
    initial_count = db.count

    db.load(input_path)
    added = db.count - initial_count
    print(f"Imported {added} objects from {input_path} (total: {db.count})")
    return 0


def cmd_db_cache(args: argparse.Namespace) -> int:
    """Manage cache database"""
    if args.cache_command == "location":
        cache_dir = MaxRefDB.get_cache_dir()
        db_path = MaxRefDB.get_default_db_path()
        print(f"Cache directory: {cache_dir}")
        print(f"Database path: {db_path}")
        if db_path.exists():
            db = MaxRefDB(auto_populate=False)
            print(f"Status: Populated with {db.count} objects")
        else:
            print("Status: Not initialized")
        return 0

    elif args.cache_command == "init":
        db_path = MaxRefDB.get_default_db_path()
        if db_path.exists() and not args.force:
            print(f"Cache already exists at {db_path}", file=sys.stderr)
            print("Use --force to reinitialize", file=sys.stderr)
            return 1

        if db_path.exists():
            db_path.unlink()

        print(f"Initializing cache at {db_path}...")
        db = MaxRefDB(auto_populate=True)
        print(f"Cache initialized with {db.count} objects")
        return 0

    elif args.cache_command == "clear":
        db_path = MaxRefDB.get_default_db_path()
        if not db_path.exists():
            print("Cache does not exist", file=sys.stderr)
            return 1

        if not args.force:
            response = input(f"Delete cache at {db_path}? [y/N]: ")
            if response.lower() != 'y':
                print("Cancelled")
                return 0

        db_path.unlink()
        print(f"Cache cleared: {db_path}")
        return 0

    else:
        print(f"Unknown cache subcommand: {args.cache_command}", file=sys.stderr)
        return 1


def cmd_serve(args: argparse.Namespace) -> int:
    """Start interactive WebSocket server for a patcher."""
    import asyncio

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    # Check if websockets is installed
    try:
        import websockets
    except ImportError:
        print("Error: websockets package required for server.", file=sys.stderr)
        print("Install with: pip install websockets", file=sys.stderr)
        return 1

    # Load patcher
    patcher = Patcher.from_file(input_path)
    _coerce_rect(patcher)

    # Start interactive server
    try:
        print(f"Starting server for: {input_path}")
        print(f"HTTP server: http://localhost:{args.port}")
        print(f"WebSocket server: ws://localhost:{args.port + 1}")
        print("Interactive editing enabled - changes sync bidirectionally")
        if not args.no_save:
            print(f"Auto-save enabled: changes will be saved to {input_path}")
        print("Press Ctrl+C to stop")

        async def run_server():
            server = await patcher.serve(
                port=args.port,
                auto_open=not args.no_open
            )
            # Keep running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping server...")
                await server.stop()

        asyncio.run(run_server())
        return 0

    except KeyboardInterrupt:
        print("\nStopping server...")
        return 0
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_preview(args: argparse.Namespace) -> int:
    """Generate SVG preview of a patcher."""
    import webbrowser
    import tempfile

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    # Load patcher
    patcher = Patcher.from_file(input_path)
    _coerce_rect(patcher)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Use temporary file
        temp_dir = Path(tempfile.gettempdir())
        output_path = temp_dir / f"{input_path.stem}_preview.svg"

    # Export to SVG
    try:
        title = args.title or input_path.name
        export_svg(
            patcher,
            output_path,
            show_ports=args.show_ports,
            title=title if not args.no_title else None,
        )
        print(f"SVG preview saved to: {output_path}")

        # Open in browser if requested
        if args.open:
            print("Opening preview in browser...")
            webbrowser.open(f"file://{output_path.absolute()}")

        return 0

    except Exception as e:
        print(f"Error generating SVG preview: {e}", file=sys.stderr)
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

    serve_parser = subparsers.add_parser("serve", help="Start interactive server with live preview")
    serve_parser.add_argument("input", help="Input .maxpat file")
    serve_parser.add_argument("--port", type=int, default=8000, help="HTTP server port (default: 8000, WebSocket on port+1)")
    serve_parser.add_argument("--no-open", action="store_true", help="Don't automatically open browser")
    serve_parser.add_argument("--no-save", action="store_true", help="Disable auto-save on changes")
    serve_parser.set_defaults(func=cmd_serve)

    preview_parser = subparsers.add_parser("preview", help="Generate SVG preview of a patcher")
    preview_parser.add_argument("input", help="Input .maxpat file")
    preview_parser.add_argument("-o", "--output", help="Output SVG file path (default: /tmp/<name>_preview.svg)")
    preview_parser.add_argument("--title", help="Custom title for the SVG")
    preview_parser.add_argument("--no-title", action="store_true", help="Don't show title in SVG")
    preview_parser.add_argument("--no-ports", dest="show_ports", action="store_false", default=True, help="Don't show inlet/outlet ports")
    preview_parser.add_argument("--open", action="store_true", help="Open preview in web browser")
    preview_parser.set_defaults(func=cmd_preview)

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

    # Database (db) command
    db_parser = subparsers.add_parser("db", help="Manage MaxRefDB databases")
    db_subparsers = db_parser.add_subparsers(dest="db_command")

    # db create
    db_create = db_subparsers.add_parser("create", help="Create a new MaxRefDB database")
    db_create.add_argument("database", help="Database file path (e.g., maxref.db)")
    db_create.add_argument("--category", choices=['max', 'msp', 'jit', 'm4l'], help="Populate with specific category")
    db_create.add_argument("--empty", action="store_true", help="Create empty database without populating")
    db_create.add_argument("--force", action="store_true", help="Overwrite existing database")
    db_create.set_defaults(func=cmd_db)

    # db populate
    db_populate = db_subparsers.add_parser("populate", help="Populate existing database with objects")
    db_populate.add_argument("database", help="Database file path")
    db_populate.add_argument("--category", choices=['max', 'msp', 'jit', 'm4l'], help="Populate with specific category")
    db_populate.add_argument("--objects", nargs="+", help="Specific object names to add")
    db_populate.set_defaults(func=cmd_db)

    # db info
    db_info = db_subparsers.add_parser("info", help="Show database information")
    db_info.add_argument("database", help="Database file path")
    db_info.add_argument("--summary", action="store_true", help="Show category summary")
    db_info.add_argument("--list", action="store_true", help="List all object names")
    db_info.add_argument("--categories", action="store_true", help="List all categories")
    db_info.set_defaults(func=cmd_db)

    # db search
    db_search = db_subparsers.add_parser("search", help="Search for objects in database")
    db_search.add_argument("database", help="Database file path")
    db_search.add_argument("query", nargs="?", help="Search query")
    db_search.add_argument("--category", help="Search within specific category")
    db_search.add_argument("--fields", help="Comma-separated fields to search (name,digest,description)")
    db_search.add_argument("-v", "--verbose", action="store_true", help="Show object digests")
    db_search.set_defaults(func=cmd_db)

    # db query
    db_query = db_subparsers.add_parser("query", help="Get detailed object information")
    db_query.add_argument("database", help="Database file path")
    db_query.add_argument("name", help="Object name to query")
    db_query.add_argument("--json", action="store_true", help="Output as JSON")
    db_query.add_argument("--dict", action="store_true", help="Output as Python dict")
    db_query.set_defaults(func=cmd_db)

    # db export
    db_export = db_subparsers.add_parser("export", help="Export database to JSON")
    db_export.add_argument("database", help="Database file path")
    db_export.add_argument("output", help="Output JSON file path")
    db_export.add_argument("--force", action="store_true", help="Overwrite existing output file")
    db_export.set_defaults(func=cmd_db)

    # db import
    db_import = db_subparsers.add_parser("import", help="Import JSON data into database")
    db_import.add_argument("database", help="Database file path")
    db_import.add_argument("input", help="Input JSON file path")
    db_import.set_defaults(func=cmd_db)

    # db cache
    db_cache = db_subparsers.add_parser("cache", help="Manage cache database")
    cache_subparsers = db_cache.add_subparsers(dest="cache_command")

    # db cache location
    cache_location = cache_subparsers.add_parser("location", help="Show cache location and status")
    cache_location.set_defaults(func=cmd_db)

    # db cache init
    cache_init = cache_subparsers.add_parser("init", help="Initialize/reinitialize cache")
    cache_init.add_argument("--force", action="store_true", help="Force reinitialize existing cache")
    cache_init.set_defaults(func=cmd_db)

    # db cache clear
    cache_clear = cache_subparsers.add_parser("clear", help="Clear cache database")
    cache_clear.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    cache_clear.set_defaults(func=cmd_db)

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
