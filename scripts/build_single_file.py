#!/usr/bin/env python3
"""Generate the single-file edition of py2max at scripts/py2max.py.

The output is a dependency-free amalgamation of the package's core object model,
layout managers, linter and .amxd support, plus an offline maxref shim carrying
port/attribute data for every documented Max object. It exists for environments
where installing a package is not an option; everything it contains is generated
from the package sources, so it cannot drift.

Usage:
    python scripts/build_single_file.py              # write scripts/py2max.py
    python scripts/build_single_file.py --check      # fail if the file is stale
    python scripts/build_single_file.py -o /tmp/x.py # write elsewhere

How it works
------------
Each source module is emitted in dependency order with its intra-package imports
removed: once every symbol lives in one namespace, `from .box import Box` is
satisfied by construction. Module-qualified references (`maxref.get_object_info`,
`porttypes.BANG`, `category.INPUT_OBJECTS`, `layout_module.GridLayoutManager`)
keep working because the generated file aliases those names to its own module
object, so attribute lookup resolves in the flattened namespace.

The maxref data layer -- normally XML parsing plus a 1 MB documentation bundle --
is replaced by a compact table distilled from that bundle at build time: port
types, method names and attribute names, with all prose dropped. Everything that
reasons *about* that data (`porttypes`, `legacy`, `category`, and the thin parser
accessors) is included verbatim rather than reimplemented, so the shim cannot
diverge from the package's validation behaviour.
"""

from __future__ import annotations

import argparse
import ast
import base64
import gzip
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "scripts" / "py2max.py"

# Emitted in this order. `None` means "the whole module"; a list means "only
# these top-level symbols". The order is hand-maintained rather than derived:
# the graph is small and stable, and an explicit list is reviewable.
Spec = Tuple[str, Optional[Sequence[str]]]

MODULES: List[Spec] = [
    ("py2max/exceptions.py", None),
    ("py2max/log.py", None),
    ("py2max/utils.py", None),
    ("py2max/core/common.py", None),
    ("py2max/core/colors.py", None),
    ("py2max/core/props.py", None),
    ("py2max/core/abstract.py", None),
    # maxref layer: curated data and port logic verbatim, data source shimmed.
    ("py2max/maxref/legacy.py", None),
    ("py2max/maxref/category.py", None),
    "SHIM",  # type: ignore[list-item]
    (
        "py2max/maxref/parser.py",
        [
            "get_legacy_defaults",
            "validate_connection",
            "get_inlet_count",
            "get_outlet_count",
            "get_inlet_types",
            "get_outlet_types",
            "MaxClassDefaults",
            "MAXCLASS_DEFAULTS",
        ],
    ),
    ("py2max/maxref/porttypes.py", None),
    # core object model
    ("py2max/core/box.py", None),
    ("py2max/core/patchline.py", None),
    ("py2max/core/serialization.py", None),
    ("py2max/core/factory.py", None),
    # layout managers (external.py is excluded: needs third-party backends)
    ("py2max/layout/graph.py", None),
    ("py2max/layout/base.py", None),
    ("py2max/layout/grid.py", None),
    ("py2max/layout/flow.py", None),
    ("py2max/layout/matrix.py", None),
    ("py2max/core/patcher.py", None),
    ("py2max/lint.py", None),
    ("py2max/m4l.py", None),
    # SVG export is pure stdlib (html/pathlib), so it comes along; Patcher.to_svg
    # would otherwise be a call to an undefined name.
    ("py2max/export/svg.py", None),
]

# Names the flattened module aliases to itself so module-qualified references
# survive amalgamation.
SELF_ALIASES = ["maxref", "porttypes", "category", "layout_module"]

# Per-module symbol renames, applied to that module's emitted text. Needed where
# the package relies on an import alias to keep two same-named symbols apart:
# `maxref/legacy.py` defines the curated MAXCLASS_DEFAULTS dict, which parser.py
# imports `as LEGACY_DEFAULTS` while exporting its own MAXCLASS_DEFAULTS lookup
# object under the historical name. Flattening needs the two spelled apart.
RENAMES: Dict[str, Dict[str, str]] = {
    "py2max/maxref/legacy.py": {"MAXCLASS_DEFAULTS": "LEGACY_DEFAULTS"},
}

# GraphLayoutManager is excluded with layout/external.py; Patcher.set_layout_mgr
# refers to it for `layout="graph:*"`, which must fail with a clear message.
GRAPH_STUB = '''
class GraphLayoutManager:  # pragma: no cover - excluded from the single file
    """Placeholder: graph layouts need third-party backends.

    ``layout="graph:*"`` requires networkx/pygraphviz/ogdf and therefore cannot
    ship in a dependency-free single file. Install the full package for it:
    ``pip install "py2max[graph]"``.
    """

    def __init__(self, *args: Any, **kwds: Any) -> None:
        raise NotImplementedError(
            "graph layouts are not available in the single-file edition of "
            'py2max; install the full package: pip install "py2max[graph]"'
        )
'''

# py2max/js2max_runtime.py is excluded: the single file cannot carry 160 KB of
# bundled JavaScript, and the runtime is package *data* rather than code, so
# there is nothing to amalgamate. `add_v8_bridge` refers to both names below.
JS2MAX_STUB = '''
#: Filename of the js2max drop-in build, as a patch refers to it.
V8_BUNDLE = "js2max.v8.js"


class _JS2MaxRuntimeStub:  # pragma: no cover - excluded from the single file
    """Placeholder: the js2max runtime is package *data*, not code.

    The two bundles are 160 KB of built JavaScript. A single file whose point is
    to be one readable, dependency-free module cannot carry them, and there is
    nothing to amalgamate in any case -- they are assets, not Python.

    ``add_v8_bridge()`` still builds the box, so a patch can be generated here
    and the runtime placed beside it by hand. Pass its filename with
    ``add_v8_bridge(bundle=...)`` and nothing is installed for you.
    """

    V8_BUNDLE = V8_BUNDLE

    @staticmethod
    def path(flavor: str = "v8") -> Any:
        raise NotImplementedError(_JS2MaxRuntimeStub._message)

    @staticmethod
    def install(dest: Any, flavor: str = "v8") -> Any:
        raise NotImplementedError(_JS2MaxRuntimeStub._message)

    _message = (
        "the js2max runtime is not bundled in the single-file edition of "
        "py2max; install the full package (pip install py2max), or copy "
        "js2max.v8.js beside the patch yourself and name it with "
        "add_v8_bridge(bundle=...)"
    )


js2max_runtime = _JS2MaxRuntimeStub()
'''

PUBLIC_API = [
    "Patcher",
    "Box",
    "Patchline",
    "Rect",
    "LayoutManager",
    "GridLayoutManager",
    "HorizontalLayoutManager",
    "VerticalLayoutManager",
    "FlowLayoutManager",
    "MatrixLayoutManager",
    "ColumnarLayoutManager",
    "lint",
    "Finding",
]


# ---------------------------------------------------------------------------
# maxref data distillation


def build_maxref_table() -> Dict[str, Dict[str, Any]]:
    """Distill the maxref bundle down to what the included code consumes.

    Port types drive validation, method names drive inlet acceptance, attribute
    names drive ``validate_attrs``. Every piece of prose (digests, descriptions,
    examples, see-also) is dropped -- that is where the bundle's ~8 MB lives.
    """
    sys.path.insert(0, str(ROOT))
    from py2max.maxref import get_available_objects, get_object_info

    table: Dict[str, Dict[str, Any]] = {}
    for name in get_available_objects():
        info = get_object_info(name)
        if not info:
            continue
        table[name] = {
            "it": [i.get("type", "") for i in (info.get("inlets") or [])],
            "ot": [o.get("type", "") for o in (info.get("outlets") or [])],
            "m": sorted(info.get("methods", {}) or {}),
            "a": sorted(info.get("attributes", {}) or {}),
        }
    return table


def render_shim(table: Dict[str, Dict[str, Any]]) -> str:
    raw = json.dumps(table, separators=(",", ":"), sort_keys=True).encode()
    # mtime=0: gzip stores a timestamp in its header by default, which would make
    # every build produce a different blob and the staleness check meaningless.
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=9, mtime=0) as f:
        f.write(raw)
    blob = base64.b64encode(buffer.getvalue()).decode()
    chunks = [blob[i : i + 88] for i in range(0, len(blob), 88)]
    literal = "\n".join(f'    "{c}"' for c in chunks)
    return f'''
# ---------------------------------------------------------------------------
# Offline maxref data layer (generated)
#
# In the package this is XML parsing over a Max installation with a 1 MB
# documentation bundle as fallback. Here it is a distilled table: port types,
# method names and attribute names for {len(table)} objects, with all prose
# dropped. Enough for connection validation, port counts, object defaults and
# attribute checking; not enough for help() -- see get_object_help below.

_MAXREF_BLOB = (
{literal}
)

_MAXREF_TABLE: Optional[Dict[str, Any]] = None


def _maxref_table() -> Dict[str, Any]:
    """Decode the embedded table on first use."""
    global _MAXREF_TABLE
    if _MAXREF_TABLE is None:
        _MAXREF_TABLE = json.loads(gzip.decompress(base64.b64decode(_MAXREF_BLOB)))
    return _MAXREF_TABLE


def get_object_info(name: str) -> Optional[Dict[str, Any]]:
    """Structured info for a Max object, or None if it is unknown.

    Shaped like the package's parser output for the keys the included code
    reads. Prose keys (digest/description/examples/seealso) are absent.
    """
    entry = _maxref_table().get(name)
    if entry is None:
        return None
    return {{
        "name": name,
        "inlets": [{{"type": t}} for t in entry["it"]],
        "outlets": [{{"type": t}} for t in entry["ot"]],
        "methods": {{m: {{}} for m in entry["m"]}},
        "attributes": {{a: {{}} for a in entry["a"]}},
    }}


def get_available_objects() -> List[str]:
    """Every Max object the embedded table knows about."""
    return sorted(_maxref_table())


def get_object_help(name: str) -> str:
    """Documentation is not embedded; point at the full package."""
    known = name in _maxref_table()
    return (
        f"No documentation for {{name!r}} in the single-file edition of py2max"
        + ("" if known else " (unknown object)")
        + ".\\nInstall the full package for help(): pip install py2max"
    )
'''


# ---------------------------------------------------------------------------
# per-module transformation


class Module:
    """One source module, reduced to the lines that belong in the output."""

    def __init__(self, path: Path, keep: Optional[Sequence[str]]) -> None:
        self.path = path
        self.keep = set(keep) if keep is not None else None
        self.renames = RENAMES.get(str(path.relative_to(ROOT)), {})
        self.src = path.read_text()
        self.lines = self.src.splitlines()
        self.tree = ast.parse(self.src)
        self.stdlib_imports: Set[str] = set()
        self.future = False
        self.defined: Set[str] = set()
        # Aliased intra-package imports (`from .lint import lint as _lint_patch`)
        # lose their alias when the import is stripped; re-emit them as plain
        # assignments so the aliased name still resolves.
        self.aliases: Dict[str, str] = {}
        # Third-party imports inside `if TYPE_CHECKING:` blocks (typing_extensions'
        # `Unpack`, for one). The block itself is dropped, so these have to be
        # re-emitted or the annotations that use them become undefined names.
        self.type_only_imports: Set[str] = set()
        self._drop: Set[int] = set()  # 1-based line numbers
        self._analyze()

    # -- helpers

    def _drop_node(self, node: ast.AST) -> None:
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", None)
        if start is None or end is None:
            return
        for decorator in getattr(node, "decorator_list", []) or []:
            start = min(start, decorator.lineno)
        self._drop.update(range(start, end + 1))

    @staticmethod
    def _is_intra_package(node: ast.AST) -> bool:
        """True for an import of py2max's own modules (relative or absolute)."""
        if isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                return True
            mod = node.module or ""
            return mod == "py2max" or mod.startswith("py2max.")
        if isinstance(node, ast.Import):
            return all(
                a.name == "py2max" or a.name.startswith("py2max.") for a in node.names
            )
        return False

    def _record_stdlib(self, node: ast.AST) -> None:
        segment = ast.get_source_segment(self.src, node)
        if segment:
            self.stdlib_imports.add(" ".join(segment.split()))

    # -- analysis

    def _analyze(self) -> None:
        body = list(self.tree.body)

        # Module docstring -> replaced by a banner comment.
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
        ):
            if isinstance(body[0].value.value, str):
                self._drop_node(body[0])

        for node in body:
            # `from __future__ import annotations` is hoisted once, globally.
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                self.future = True
                self._drop_node(node)
                continue

            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if self._is_intra_package(node):
                    self._drop_node(node)
                else:
                    self._record_stdlib(node)
                    self._drop_node(node)
                continue

            # `if TYPE_CHECKING:` blocks mostly import intra-package names for
            # annotations, which resolve in the flattened namespace anyway. Any
            # *external* import in there is still needed, though, so hoist it
            # into a single TYPE_CHECKING block in the header before dropping.
            if isinstance(node, ast.If) and self._references_type_checking(node.test):
                for inner in ast.walk(node):
                    if isinstance(inner, (ast.Import, ast.ImportFrom)):
                        if not self._is_intra_package(inner):
                            segment = ast.get_source_segment(self.src, inner)
                            if segment:
                                self.type_only_imports.add(" ".join(segment.split()))
                self._drop_node(node)
                continue

            if isinstance(node, ast.Assign) and self._is_named_assign(node, "__all__"):
                self._drop_node(node)
                continue

            names = self._defines(node)
            if self.keep is not None and not (names & self.keep):
                self._drop_node(node)
                continue
            self.defined |= {self.renames.get(n, n) for n in names}

        # Function-local intra-package imports (e.g. `from py2max import maxref`
        # inside Box.help) must go too: there is no package to import from.
        for node in ast.walk(self.tree):
            if isinstance(
                node, (ast.Import, ast.ImportFrom)
            ) and self._is_intra_package(node):
                self._drop_node(node)
                for alias in node.names:
                    if alias.asname and alias.asname != alias.name:
                        self.aliases[alias.asname] = alias.name.rsplit(".", 1)[-1]

    @staticmethod
    def _references_type_checking(test: ast.expr) -> bool:
        return any(
            isinstance(n, ast.Name) and n.id == "TYPE_CHECKING" for n in ast.walk(test)
        )

    @staticmethod
    def _is_named_assign(node: ast.Assign, name: str) -> bool:
        return any(isinstance(t, ast.Name) and t.id == name for t in node.targets)

    @staticmethod
    def _defines(node: ast.AST) -> Set[str]:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            return {node.name}
        if isinstance(node, ast.Assign):
            return {t.id for t in node.targets if isinstance(t, ast.Name)}
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            return {node.target.id}
        return set()

    def render(self) -> str:
        kept = [
            line
            for number, line in enumerate(self.lines, start=1)
            if number not in self._drop
        ]
        # Collapse the runs of blank lines left behind by dropped nodes.
        out: List[str] = []
        for line in kept:
            if not line.strip() and out and not out[-1].strip():
                continue
            out.append(line)
        body = "\n".join(out)
        for old, new in self.renames.items():
            body = re.sub(rf"\b{re.escape(old)}\b", new, body)
        out = body.splitlines()

        rel = self.path.relative_to(ROOT)
        banner = [
            "",
            "# " + "-" * 74,
            f"# {rel}"
            + (
                ""
                if self.keep is None
                else f" (partial: {', '.join(sorted(self.keep))})"
            ),
            "# " + "-" * 74,
            "",
        ]
        return "\n".join(banner + out).rstrip() + "\n"


# ---------------------------------------------------------------------------
# assembly


def provenance() -> str:
    def git(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
            ).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"

    sha = git("rev-parse", "--short", "HEAD")
    dirty = " (working tree modified)" if git("status", "--porcelain") else ""
    version = "unknown"
    init = (ROOT / "py2max" / "__init__.py").read_text()
    for line in init.splitlines():
        if line.startswith("__version__"):
            version = line.split("=", 1)[1].strip().strip("\"'")
            break
    return f"py2max {version}, generated from {sha}{dirty}"


def build() -> str:
    specs: List[Spec] = []
    shim_index = None
    for entry in MODULES:
        if entry == "SHIM":
            shim_index = len(specs)
            continue
        specs.append(entry)  # type: ignore[arg-type]

    modules = [Module(ROOT / path, keep) for path, keep in specs]

    # Collision check: two modules defining the same top-level name would
    # silently shadow each other in one namespace.
    seen: Dict[str, str] = {}
    collisions: List[str] = []
    for module in modules:
        for name in sorted(module.defined):
            if name in seen:
                collisions.append(f"{name}: {seen[name]} and {module.path.name}")
            else:
                seen[name] = module.path.name
    allowed = {"logger"}  # same get_logger(__name__) call in several modules
    fatal = [c for c in collisions if c.split(":")[0] not in allowed]
    if fatal:
        raise SystemExit("top-level name collisions:\n  " + "\n  ".join(fatal))

    stdlib: Set[str] = set()
    for module in modules:
        stdlib |= module.stdlib_imports
    # The shim needs these regardless of what the sources happen to import.
    stdlib |= {
        "import base64",
        "import gzip",
        "import json",
        "import sys",
        "from typing import Any, Dict, List, Optional",
    }

    plain = sorted(s for s in stdlib if s.startswith("import "))
    froms = sorted(s for s in stdlib if s.startswith("from "))

    # Type-only third-party imports, re-emitted under one TYPE_CHECKING guard so
    # nothing is needed at runtime (typing_extensions is not a dependency).
    type_only: Set[str] = set()
    for module in modules:
        type_only |= module.type_only_imports
    type_only_block = ""
    if type_only:
        body = "\n".join(f"    {imp}" for imp in sorted(type_only))
        type_only_block = (
            "\n# Type-checking-only imports, hoisted out of the modules'\n"
            "# `if TYPE_CHECKING:` blocks. Never imported at runtime.\n"
            "if TYPE_CHECKING:\n" + body + "\n"
        )
        stdlib.add("from typing import TYPE_CHECKING")
        froms = sorted(s for s in stdlib if s.startswith("from "))

    header = f'''"""py2max: a pure python library to generate .maxpat patcher files.

GENERATED FILE -- DO NOT EDIT BY HAND.
{provenance()}
Regenerate with: python scripts/build_single_file.py

This is the single-file edition: the package's core object model, layout
managers, linter and .amxd support amalgamated into one dependency-free module,
with an offline maxref table embedded for connection validation and object
defaults.

Included: Patcher/Box/Patchline, grid/flow/columnar/matrix layouts, lint(),
connection and attribute validation, .amxd read/write, SVG export.

Not included: Box.help() documentation prose (structured get_info() data is
present), graph layouts (layout="graph:*", needs third-party backends), the CLI,
and the SQLite maxref database. For those: pip install py2max

basic usage:

    >>> p = Patcher('out.maxpat')
    >>> osc1 = p.add_textbox('cycle~ 440')
    >>> gain = p.add_textbox('gain~')
    >>> dac = p.add_textbox('ezdac~')
    >>> p.add_line(osc1, gain)
    >>> p.add_line(gain, dac)
    >>> p.save()

"""

from __future__ import annotations

'''

    parts = [header]
    parts.append("\n".join(plain) + "\n\n" + "\n".join(froms) + "\n")
    if type_only_block:
        parts.append(type_only_block)
    parts.append(
        "\n# Module-qualified references (maxref.get_object_info, porttypes.BANG,\n"
        "# category.INPUT_OBJECTS, layout_module.GridLayoutManager) resolve here:\n"
        "# every symbol lives in this one module, so alias those names to it.\n"
        f"{' = '.join(SELF_ALIASES)} = sys.modules[__name__]\n"
    )
    parts.append(f"\n__all__ = {json.dumps(PUBLIC_API, indent=4)}\n")

    rendered = [m.render() for m in modules]
    if shim_index is not None:
        rendered.insert(shim_index, render_shim(build_maxref_table()))
    parts.extend(rendered)
    parts.append(GRAPH_STUB)
    parts.append(JS2MAX_STUB)

    # Re-emit aliases lost with their stripped imports. Emitted last because the
    # targets must already be defined; every use is inside a function body, so
    # call-time resolution is unaffected by the position.
    aliases: Dict[str, str] = {}
    for module in modules:
        for asname, name in module.aliases.items():
            # Skip names another mechanism already provides: SELF_ALIASES covers
            # module aliases, RENAMES covers the legacy/parser MAXCLASS_DEFAULTS
            # split (where `LEGACY_DEFAULTS = MAXCLASS_DEFAULTS` would be wrong).
            if asname in SELF_ALIASES or asname in seen:
                continue
            aliases[asname] = name
    if aliases:
        lines = "\n".join(
            f"{asname} = {name}" for asname, name in sorted(aliases.items())
        )
        parts.append(
            "\n# Aliases from stripped intra-package imports "
            "(e.g. `from .lint import lint as _lint_patch`).\n" + lines + "\n"
        )

    return "\n".join(parts)


def postprocess(path: Path) -> None:
    """Format, lint-fix and syntax-check the generated file.

    The F821 pass is a completeness gate, not cosmetics: code kept in the
    amalgamation that calls into an *excluded* module leaves an undefined name
    behind once its import is stripped (as ``Patcher.to_svg`` did before
    ``export/svg.py`` was included). That is a NameError at call time, so the
    build must fail on it rather than emit a file with a hole in it.
    """
    for cmd in (
        ["ruff", "format", str(path)],
        ["ruff", "check", "--fix", "--quiet", str(path)],
    ):
        subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    ast.parse(path.read_text())

    undefined = subprocess.run(
        ["ruff", "check", "--select", "F821", "--quiet", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if undefined.returncode != 0:
        raise SystemExit(
            "generated file references undefined names -- an excluded module is "
            "still called from included code:\n" + undefined.stdout
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the committed file differs from a fresh build",
    )
    args = parser.parse_args()

    source = build()
    if args.check:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td) / "py2max.py"
            tmp.write_text(source)
            postprocess(tmp)
            fresh = tmp.read_text()
        current = args.output.read_text() if args.output.exists() else ""

        def strip(text: str) -> str:
            # The provenance line carries the commit sha, which legitimately
            # differs between a committed file and a fresh local build.
            return "\n".join(
                line
                for line in text.splitlines()
                if not (line.startswith("py2max ") and "generated from" in line)
            )

        if strip(fresh) != strip(current):
            print(f"{args.output} is stale; run: python {Path(__file__).name}")
            return 1
        print(f"{args.output} is up to date")
        return 0

    args.output.write_text(source)
    postprocess(args.output)
    lines = len(args.output.read_text().splitlines())
    size = args.output.stat().st_size / 1024
    print(f"wrote {args.output} ({lines:,} lines, {size:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
