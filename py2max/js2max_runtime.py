"""The js2max JavaScript runtime, shipped inside the package.

py2max generates `.maxpat` files that Max opens afterwards. `js2max` is the
other direction: it runs *inside* an open patcher through Max's ``v8`` object,
so a patch can build objects into itself and serialize itself back out. The
two halves share one description of the format.

This module makes the built JavaScript reachable from Python. Without it the
bundles exist only in the source repository, so nobody installing py2max from
PyPI can use js2max at all.

**Why the runtime ships with the package rather than being downloaded.**
``js2max/src/objects.ts`` -- the box classes, port counts and outlet types for
1098 object classes -- is generated from this package's maxref bundle. A bundle
built against one version of py2max and used with another declares wrong port
counts for whatever changed between them, and a box that declares a port it does
not have silently loses the cord attached to it when Max opens the file.
Shipping them in one artifact makes that skew impossible by construction.

The bundles are inert data. Nothing here imports or executes them, and py2max
keeps its zero runtime dependencies.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, Union

from .log import get_logger

logger = get_logger(__name__)

__all__ = ["BUNDLE_FILENAMES", "V8_BUNDLE", "install", "path"]

_DATA = Path(__file__).parent / "data" / "js2max"

#: The filename Max loads for the drop-in build. A patch referring to the
#: bridge does so by this name, so it must not be renamed on install.
V8_BUNDLE = "js2max.v8.js"

#: The two builds, by flavour.
#:
#: ``v8`` is the drop-in: ``[v8 js2max.v8.js]`` in a patch, then send it
#: messages. ``commonjs`` is for ``require("js2max.js")`` from a script of your
#: own, when the message set is not enough and you want the model and the bridge
#: directly.
BUNDLE_FILENAMES: Dict[str, str] = {
    "v8": V8_BUNDLE,
    "commonjs": "js2max.js",
}


def path(flavor: str = "v8") -> Path:
    """Return the path to a shipped bundle, inside the installed package.

    Args:
        flavor: ``"v8"`` for the drop-in build, ``"commonjs"`` for the
            ``require()``-able one.

    Returns:
        Path to the bundle within the package directory.

    Raises:
        ValueError: If ``flavor`` is not a known build.
        FileNotFoundError: If the bundle is missing from the installation,
            which means the package was built without it.
    """
    try:
        filename = BUNDLE_FILENAMES[flavor]
    except KeyError:
        known = ", ".join(sorted(BUNDLE_FILENAMES))
        raise ValueError(
            f"unknown js2max build {flavor!r}; expected one of: {known}"
        ) from None

    bundle = _DATA / filename
    if not bundle.exists():
        raise FileNotFoundError(
            f"the js2max runtime is missing from this py2max installation "
            f"(expected {bundle}). It is built by `make js2max` and shipped as "
            f"package data; a source checkout that has never been built will "
            f"not have it."
        )
    return bundle


def install(dest: Union[str, Path], flavor: str = "v8") -> Path:
    """Copy a bundle to ``dest``, so a patch beside it can load it.

    Max resolves a bare filename like ``js2max.v8.js`` through its search path,
    which includes the folder holding the patch -- so a patch and its runtime
    sitting in the same directory need no configuration at all. That is what
    this is for.

    Args:
        dest: Directory to copy into, or the full destination file path. A
            directory is created if it does not exist.
        flavor: Which build to install. See :data:`BUNDLE_FILENAMES`.

    Returns:
        Path to the installed copy.
    """
    source = path(flavor)
    target = Path(dest)

    # A directory, or a file path? An existing directory is unambiguous; so is
    # a path with no suffix, which nobody means as a filename for a `.js` file.
    if target.is_dir() or not target.suffix:
        target.mkdir(parents=True, exist_ok=True)
        target = target / source.name
    else:
        target.parent.mkdir(parents=True, exist_ok=True)

    # Skipping an identical copy keeps `save()` from rewriting the runtime on
    # every call, which matters when a script saves in a loop.
    if target.exists() and target.read_bytes() == source.read_bytes():
        logger.debug(f"js2max runtime already current at {target}")
        return target

    shutil.copyfile(source, target)
    logger.debug(f"installed js2max runtime to {target}")
    return target
