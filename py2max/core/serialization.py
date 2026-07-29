"""Serialization mixin for the Patcher class.

Holds the instance-serialization methods (``to_dict``, ``to_json``, ``save``,
``save_as``) extracted from ``Patcher`` to keep that class focused on the
object graph and layout. These are mixed into ``Patcher`` via inheritance, so
they remain ordinary ``Patcher`` methods with no API change.

The alternative constructors ``from_dict``/``from_file`` stay on ``Patcher``
itself, since they construct the concrete class.
"""

import json
from pathlib import Path
from typing import Any, Dict, Union

from ..exceptions import PatcherIOError
from ..log import get_logger, log_operation
from .abstract import AbstractPatcher
from .common import rects_to_lists

logger = get_logger(__name__)


class SerializationMixin(AbstractPatcher):
    """Instance serialization (to dict/json and saving to disk) for Patcher."""

    def to_dict(self) -> Dict[str, Any]:
        """Return the patcher as a ``.maxpat`` dictionary.

        Renders first, so the result is the patcher as it stands rather than as
        it stood after whatever last happened to render it. It did not, and the
        failure was silent and order-dependent: ``to_dict()`` returned a patcher
        with *no boxes* until something else called ``render()``, and the same
        call on the same object then started returning them. A test asserting
        over ``to_dict()`` examined an empty patcher and passed for the wrong
        reason, which is how this was found.

        Rendering here also removes the asymmetry with ``Box.to_dict()``, which
        has always returned a populated box with no preparation required.
        """
        self.render()
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        rects_to_lists(d)
        if not self._parent:
            return dict(patcher=d)
        return d

    def to_json(self) -> str:
        """cascade convert to json"""
        # No `render()` here: `to_dict()` does its own, and rendering twice was
        # only ever safe because it is idempotent.
        return json.dumps(self.to_dict(), indent=4)

    def save_as(self, path: Union[str, Path]) -> None:
        """Save the patch to a specified file path.

        Renders all objects and connections, then saves the patch as a
        .maxpat JSON file (or a binary .amxd) that can be opened in Max/MSP.

        Args:
            path: File path where the patch should be saved.

        Raises:
            PatcherIOError: If file cannot be written or path is invalid.
        """
        logger.debug(f"Saving patcher to: {path}")
        path = Path(path)

        # Resolve to an absolute, normalized path. This is an offline file
        # generator that writes wherever the caller asks; we deliberately do not
        # police the destination (the previous ".."/"/etc" allowlist was trivially
        # bypassable and gave a false sense of safety). We still surface genuinely
        # unresolvable paths as a clear error rather than letting them fail later.
        try:
            resolved_path = path.resolve()
        except (OSError, RuntimeError) as e:
            raise PatcherIOError(
                f"Invalid file path: {path}", file_path=str(path), operation="validate"
            ) from e

        try:
            # Create parent directories if needed
            if resolved_path.parent:
                resolved_path.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created parent directories: {resolved_path.parent}")

            with log_operation(
                logger, "render patcher", boxes=len(self._boxes), lines=len(self._lines)
            ):
                self.render()

            self._lint_on_save()

            # Use resolved path for writing
            if resolved_path.suffix.lower() == ".amxd":
                # Lazy import: m4l is a feature layer, kept off core's import path.
                from py2max.m4l import ensure_amxd_project_block, pack_amxd

                patcher_dict = self.to_dict()
                ensure_amxd_project_block(patcher_dict, device_type=self._device_type)
                payload = json.dumps(patcher_dict, indent=4)
                resolved_path.write_bytes(
                    pack_amxd(
                        payload,
                        device_type=self._device_type,
                        patcher_filename=resolved_path.stem + ".maxpat",
                    )
                )
            else:
                with open(resolved_path, "w", encoding="utf8") as f:
                    json.dump(self.to_dict(), f, indent=4)

            # A patch holding a [v8 js2max.v8.js] box needs that file beside
            # it, or it opens with a broken object. Only patchers that asked for
            # the bridge get one, so an ordinary save never writes a second file.
            if getattr(self, "_needs_js2max_runtime", False):
                from py2max import js2max_runtime

                installed = js2max_runtime.install(resolved_path.parent)
                logger.info(f"Installed js2max runtime: {installed}")

            logger.info(
                f"Saved patcher to: {resolved_path} ({len(self._boxes)} objects, {len(self._lines)} connections)"
            )

        except IOError as e:
            logger.error(f"Failed to write patcher to: {resolved_path}")
            raise PatcherIOError(
                "Failed to write patcher file",
                file_path=str(resolved_path),
                operation="write",
            ) from e

    def _lint_on_save(self) -> None:
        """Lint the top-level patch on save.

        Error-severity findings (bad connections, out-of-range ports, orphaned
        lines, duplicate IDs) are logged. When the patcher was created with
        ``strict=True`` they are raised as ``InvalidPatchError`` instead. Layout
        warnings (overlaps / off-canvas / unknown objects) are left to an
        explicit ``lint()`` call or ``py2max validate`` to keep saves quiet.
        """
        if self._parent:  # only lint the top-level patcher
            return
        from ..lint import lint as _lint_patch

        errors = [f for f in _lint_patch(self) if f.severity == "error"]
        if not errors:
            return
        for finding in errors:
            logger.warning("lint: %s", finding)
        if getattr(self, "_strict", False):
            from ..exceptions import InvalidPatchError

            raise InvalidPatchError(
                f"patch has {len(errors)} validation error(s); first: {errors[0]}"
            )

    def save(self) -> None:
        """Save the patch to the default file path.

        Uses the path specified during Patcher creation. If no path
        was specified, this method will do nothing. Pending associated
        comments are flushed during ``render`` (called by ``save_as``), so
        every serialization path emits them.
        """
        if self._path:
            self.save_as(self._path)
