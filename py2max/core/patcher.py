"""Patcher class for creating and managing Max/MSP patches.

This module contains the main Patcher class for creating Max/MSP patches
programmatically with automatic layout management and connection validation.

Example:
    >>> p = Patcher('out.maxpat')
    >>> osc1 = p.add_textbox('cycle~ 440')
    >>> gain = p.add_textbox('gain~')
    >>> dac = p.add_textbox('ezdac~')
    >>> p.add_line(osc1, gain)
    >>> p.add_line(gain, dac)
    >>> p.save()
"""

import json
from pathlib import Path
from typing import List, Optional, Tuple, Union, cast

from py2max import layout as layout_module
from py2max import maxref
from py2max.exceptions import InvalidConnectionError, PatcherIOError
from py2max.log import get_logger, log_operation

from .abstract import AbstractBox, AbstractLayoutManager, AbstractPatcher, AbstractPatchline
from .box import Box
from .common import Rect
from .patchline import Patchline

# ---------------------------------------------------------------------------
# CONSTANTS

MAX_VER_MAJOR = 8
MAX_VER_MINOR = 5
MAX_VER_REVISION = 5

# Module logger
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Primary Classes


class Patcher(AbstractPatcher):
    """Core class for creating and managing Max/MSP patches.

    The Patcher class provides a high-level interface for creating Max/MSP patches
    programmatically. It handles object positioning, connection validation, and
    automatic layout management.

    Features:
        - Automatic object positioning with multiple layout managers
        - Connection validation using Max object metadata
        - Support for all major Max object types
        - Hierarchical patch organization with subpatchers
        - Export to .maxpat file format

    Args:
        path: Output file path for the patch.
        title: Optional title for the patch.
        parent: Parent patcher for hierarchical organization.
        classnamespace: Namespace for object classes (e.g., 'rnbo').
        reset_on_render: Whether to reset layout on render.
        layout: Layout manager type ('horizontal', 'vertical', 'grid', 'flow', 'matrix').
        auto_hints: Whether to automatically generate object hints.
        openinpresentation: Presentation mode setting.
        validate_connections: Whether to validate patchline connections.
        flow_direction: Direction for flow-based layouts ('horizontal', 'vertical').
        cluster_connected: Whether to cluster connected objects in grid layout.
        num_dimensions: Number of rows used by the matrix layout (also treated as column count when flow_direction='column').
        dimension_spacing: Spacing between rows/columns for matrix layout variants.
        semantic_ids: Whether to generate semantic IDs based on object names (e.g., 'cycle_1')
                     instead of numeric IDs (e.g., 'obj-1'). Enables more readable debugging.

    Example:
        >>> p = Patcher('my-patch.maxpat', layout='grid')
        >>> osc = p.add_textbox('cycle~ 440')
        >>> gain = p.add_textbox('gain~')
        >>> p.add_line(osc, gain)
        >>> p.save()

        >>> # With semantic IDs
        >>> p = Patcher('my-patch.maxpat', semantic_ids=True)
        >>> osc1 = p.add_textbox('cycle~ 440')  # ID: 'cycle_1'
        >>> osc2 = p.add_textbox('cycle~ 220')  # ID: 'cycle_2'
        >>> gain = p.add_textbox('gain~')       # ID: 'gain_1'
    """

    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        title: Optional[str] = None,
        parent: Optional["Patcher"] = None,
        classnamespace: Optional[str] = None,
        reset_on_render: bool = True,
        layout: str = "horizontal",
        auto_hints: bool = False,
        openinpresentation: int = 0,
        validate_connections: bool = False,
        flow_direction: str = "horizontal",
        cluster_connected: bool = False,
        # Matrix layout configuration parameters
        num_dimensions: int = 4,
        dimension_spacing: float = 100.0,
        semantic_ids: bool = False,
    ):
        logger.debug(
            f"Initializing Patcher: path={path}, layout={layout}, "
            f"validate_connections={validate_connections}, semantic_ids={semantic_ids}"
        )
        self._path = path
        self._parent = parent
        self._node_ids: list[str] = []  # ids by order of creation
        self._objects: dict[str, AbstractBox] = {}  # dict of objects by id
        self._boxes: list[AbstractBox] = []  # store child objects (boxes, etc.)
        self._lines: list[AbstractPatchline] = []  # store patchline objects
        self._edge_ids: list[tuple[str, str]] = []  # store edge-ids by order of creation
        self._id_counter = 0
        self._link_counter = 0
        self._last_link: Optional[tuple[str, str]] = None
        self._reset_on_render = reset_on_render
        self._semantic_ids = semantic_ids
        self._semantic_counters: dict[str, int] = {}  # Track counts per object type
        self._flow_direction = flow_direction
        self._cluster_connected = cluster_connected
        self._num_dimensions = num_dimensions
        self._dimension_spacing = dimension_spacing
        self._layout_mgr: AbstractLayoutManager = self.set_layout_mgr(layout)
        self._auto_hints = auto_hints
        self._validate_connections = validate_connections
        self._pending_comments: list[
            tuple[str, str, Optional[str]]
        ] = []  # [(box_id, comment_text, comment_pos), ...]
        self._maxclass_methods = {
            # specialized methods
            "m": self.add_message,  # custom -- like keyboard shortcut
            "c": self.add_comment,  # custom -- like keyboard shortcut
            "coll": self.add_coll,
            "dict": self.add_dict,
            "table": self.add_table,
            "itable": self.add_itable,
            "umenu": self.add_umenu,
            "bpatcher": self.add_bpatcher,
        }
        # --------------------------------------------------------------------
        # begin max attributes
        if title:  # not a default attribute
            self.title = title
        self.fileversion: int = 1
        self.appversion = {
            "major": MAX_VER_MAJOR,
            "minor": MAX_VER_MINOR,
            "revision": MAX_VER_REVISION,
            "architecture": "x64",
            "modernui": 1,
        }
        self.classnamespace = classnamespace or "box"
        self.rect = Rect(85.0, 104.0, 640.0, 480.0)
        self.bglocked = 0
        self.openinpresentation = openinpresentation
        self.default_fontsize = 12.0
        self.default_fontface = 0
        self.default_fontname = "Arial"
        self.gridonopen = 1
        self.gridsize = [15.0, 15.0]
        self.gridsnaponopen = 1
        self.objectsnaponopen = 1
        self.statusbarvisible = 2
        self.toolbarvisible = 1
        self.lefttoolbarpinned = 0
        self.toptoolbarpinned = 0
        self.righttoolbarpinned = 0
        self.bottomtoolbarpinned = 0
        self.toolbars_unpinned_last_save = 0
        self.tallnewobj = 0
        self.boxanimatetime = 200
        self.enablehscroll = 1
        self.enablevscroll = 1
        self.devicewidth = 0.0
        self.description = ""
        self.digest = ""
        self.tags = ""
        self.style = ""
        self.subpatcher_template = ""
        self.assistshowspatchername = 0
        self.boxes: list[dict] = []
        self.lines: list[dict] = []
        # self.parameters: dict = {}
        self.dependency_cache: list = []
        self.autosave = 0

    def __repr__(self):
        return f"{self.__class__.__name__}(path='{self._path}')"

    def __iter__(self):
        yield self
        for box in self._boxes:
            yield from iter(box)

    def find_by_id(self, box_id: str) -> Optional["Box"]:
        """Find a box by its ID.

        Args:
            box_id: The ID of the box to find.

        Returns:
            The Box object if found, None otherwise.

        Example:
            >>> p = Patcher('patch.maxpat')
            >>> osc = p.add_textbox('cycle~ 440')
            >>> found = p.find_by_id(osc.id)
            >>> assert found is osc
        """
        return cast(Optional["Box"], self._objects.get(box_id))

    def find_by_type(self, maxclass: str) -> List["Box"]:
        """Find all boxes of a specific Max object type.

        Args:
            maxclass: The Max object class name (e.g., 'newobj', 'message', 'comment').

        Returns:
            List of Box objects matching the type.

        Example:
            >>> p = Patcher('patch.maxpat')
            >>> p.add_textbox('cycle~ 440')
            >>> p.add_textbox('saw~ 220')
            >>> p.add_message('bang')
            >>> oscillators = [b for b in p.find_by_type('newobj')
            ...                if 'cycle~' in b.text or 'saw~' in b.text]
            >>> assert len(oscillators) == 2
        """
        return cast(
            List["Box"],
            [box for box in self._boxes if getattr(box, "maxclass", None) == maxclass],
        )

    def find_by_text(self, pattern: str, case_sensitive: bool = False) -> List["Box"]:
        """Find all boxes whose text matches a pattern.

        Args:
            pattern: The text pattern to search for (substring match).
            case_sensitive: Whether the search should be case-sensitive (default: False).

        Returns:
            List of Box objects whose text contains the pattern.

        Example:
            >>> p = Patcher('patch.maxpat')
            >>> p.add_textbox('cycle~ 440')
            >>> p.add_textbox('saw~ 220')
            >>> p.add_textbox('gain~ 0.5')
            >>> oscillators = p.find_by_text('~')
            >>> assert len(oscillators) == 3
            >>> just_cycle = p.find_by_text('cycle')
            >>> assert len(just_cycle) == 1
        """
        results = []
        for box in self._boxes:
            text = getattr(box, "text", "") or ""
            if not case_sensitive:
                if pattern.lower() in text.lower():
                    results.append(box)
            else:
                if pattern in text:
                    results.append(box)
        return cast(List["Box"], results)

    @property
    def filepath(self) -> Union[str, Path]:
        if self._path is None:
            return ""
        return self._path

    @property
    def width(self) -> float:
        """width of patcher window."""
        return self.rect.w

    @property
    def height(self) -> float:
        """height of patcher windows."""
        return self.rect.h

    @classmethod
    def from_dict(cls, patcher_dict: dict, save_to: Optional[str] = None) -> "Patcher":
        """create a patcher instance from a dict"""

        if save_to:
            patcher = cls(save_to)
        else:
            patcher = cls()
        patcher.__dict__.update(patcher_dict)

        for box_dict in patcher.boxes:
            box = box_dict["box"]
            b = Box.from_dict(box)
            assert b.id, "box must have id"
            patcher._objects[b.id] = b
            # b = patcher.box_from_dict(box)
            patcher._boxes.append(b)

            # Set parent reference for nested subpatchers
            if hasattr(b, "_patcher") and b._patcher is not None:
                b._patcher._parent = patcher

        for line_dict in patcher.lines:
            line = line_dict["patchline"]
            pl = Patchline.from_dict(line)
            patcher._lines.append(pl)

        return patcher

    @classmethod
    def from_file(
        cls, path: Union[str, Path], save_to: Optional[str] = None
    ) -> "Patcher":
        """create a patcher instance from a .maxpat json file"""

        with open(path, encoding="utf8") as f:
            maxpat = json.load(f)
        return Patcher.from_dict(maxpat["patcher"], save_to)

    def to_dict(self) -> dict:
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        if not self._parent:
            return dict(patcher=d)
        return d

    def to_json(self) -> str:
        """cascade convert to json"""
        self.render()
        return json.dumps(self.to_dict(), indent=4)

    def find(self, text: str) -> Optional["Box"]:
        """Find box object by maxclass or text pattern.

        Recursively searches through all objects in the patch to find
        one matching the specified maxclass or text pattern.

        Args:
            text: The maxclass name or text pattern to search for.

        Returns:
            The first matching Box object, or None if not found.
        """
        for obj in self:
            if not isinstance(obj, Patcher):
                if obj.maxclass == text:
                    return obj
                if hasattr(obj, "text"):
                    if obj.text and obj.text.startswith(text):
                        return obj
        return None

    def find_box(self, text: str) -> Optional["Box"]:
        """find box object by maxclass or type

        returns box if found else None
        """
        for box in self._objects.values():
            if box.maxclass == text:
                return cast("Box", box)
            if hasattr(box, "text"):
                if box.text and box.text.startswith(text):
                    return cast("Box", box)
        return None

    def find_box_with_index(self, text: str) -> Optional[Tuple[int, "Box"]]:
        """find box object by maxclass or type

        returns (index, box) if found
        """
        for i, box in enumerate(self._boxes):
            if box.maxclass == text:
                return (i, cast("Box", box))
            if hasattr(box, "text"):
                if box.text and box.text.startswith(text):
                    return (i, cast("Box", box))
        return None

    def render(self, reset: bool = False) -> None:
        """cascade convert py2max objects to dicts."""
        if reset or self._reset_on_render:
            self.boxes = []
            self.lines = []
        for box in self._boxes:
            box.render()
            self.boxes.append(box.to_dict())
        self.lines = [line.to_dict() for line in self._lines]

    def save_as(self, path: Union[str, Path]) -> None:
        """Save the patch to a specified file path with security validation.

        Renders all objects and connections, then saves the patch as a
        .maxpat JSON file that can be opened in Max/MSP.

        Args:
            path: File path where the patch should be saved.

        Raises:
            PatcherIOError: If file cannot be written or path is invalid.
        """
        logger.debug(f"Saving patcher to: {path}")
        path = Path(path)

        # Security: Validate path to prevent path traversal attacks
        try:
            # Check for suspicious path components BEFORE resolving
            path_str = str(path)
            if (
                ".." in path.parts
                or path_str.startswith("/etc")
                or path_str.startswith("/sys")
            ):
                raise PatcherIOError(
                    f"Invalid path detected (potential path traversal): {path}",
                    file_path=str(path),
                    operation="validate",
                )

            # Resolve path to absolute and normalize it
            resolved_path = path.resolve()

            # Check for path traversal attempts
            # Ensure the resolved path is within the current working directory or user-specified location
            # This prevents attacks like ../../etc/passwd
            if not resolved_path.is_absolute():
                raise PatcherIOError(
                    f"Path must resolve to absolute path: {path}",
                    file_path=str(path),
                    operation="validate",
                )

        except PatcherIOError:
            # Re-raise PatcherIOError exceptions as-is
            raise
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

            # Use resolved path for writing
            with open(resolved_path, "w", encoding="utf8") as f:
                json.dump(self.to_dict(), f, indent=4)

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

    def save(self) -> None:
        """Save the patch to the default file path.

        Uses the path specified during Patcher creation. If no path
        was specified, this method will do nothing. Before saving,
        processes any pending associated comments to ensure they are
        positioned correctly relative to their boxes.
        """
        # Process pending comments before saving
        self._process_pending_comments()

        if self._path:
            self.save_as(self._path)

    async def serve(self, port: int = 8000, auto_open: bool = True):
        """Start an interactive WebSocket server for this patcher.

        Opens a web browser with interactive editor that allows bidirectional
        editing between Python and the browser. Supports drag-and-drop,
        connection drawing, and object creation.

        Args:
            port: HTTP server port (default: 8000, WebSocket on port+1)
            auto_open: Automatically open browser (default: True)

        Returns:
            InteractivePatcherServer instance (async context manager)

        Example:
            >>> p = Patcher('demo.maxpat')
            >>> async with await p.serve() as server:
            ...     # Edit in browser - changes sync back to Python!
            ...     await asyncio.sleep(10)

        Note:
            Requires websockets package: pip install websockets
        """
        from py2max.server import serve_interactive

        self._server = await serve_interactive(self, port, auto_open)
        return self._server

    def get_id(self, object_name: Optional[str] = None) -> str:
        """Generate object ID, optionally semantic based on object name.

        Args:
            object_name: Optional Max object name (e.g., 'cycle~', 'gain~').
                        Used to generate semantic IDs like 'cycle_1' when
                        semantic_ids mode is enabled.

        Returns:
            Object ID string (e.g., 'obj-5' or 'cycle_1').
        """
        if self._semantic_ids and object_name:
            # Sanitize object name (remove ~, spaces, special chars)
            clean_name = (
                object_name.replace("~", "")
                .replace(" ", "_")
                .replace(".", "_")
                .replace("-", "_")
                .replace("[", "")
                .replace("]", "")
                .replace("(", "")
                .replace(")", "")
            )

            # Get or increment counter for this object type
            count = self._semantic_counters.get(clean_name, 0) + 1
            self._semantic_counters[clean_name] = count
            return f"{clean_name}_{count}"
        else:
            # Standard numeric ID
            self._id_counter += 1
            return f"obj-{self._id_counter}"

    def set_layout_mgr(self, name: str) -> layout_module.LayoutManager:
        """takes a name and returns an instance of a layout manager"""
        if name == "horizontal":
            return layout_module.HorizontalLayoutManager(self)
        elif name == "vertical":
            return layout_module.VerticalLayoutManager(self)
        elif name == "flow":
            return layout_module.FlowLayoutManager(self, flow_direction=self._flow_direction)
        elif name == "grid":
            return layout_module.GridLayoutManager(
                self,
                flow_direction=self._flow_direction,
                cluster_connected=self._cluster_connected,
            )
        elif name == "matrix":
            return layout_module.MatrixLayoutManager(
                self,
                flow_direction=self._flow_direction,
                num_dimensions=self._num_dimensions,
                dimension_spacing=self._dimension_spacing,
            )
        else:
            raise NotImplementedError(f"layout '{name}' doesn't exist")

    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """get box rect (position) via maxclass or layout_manager"""
        if maxclass:
            return self._layout_mgr.get_pos(maxclass)
        return self._layout_mgr.get_pos()

    def optimize_layout(self) -> None:
        """Optimize object positions based on layout manager type.

        Calls the layout manager's optimization method to improve object
        positioning, then repositions any associated comments based on
        the new box positions. The effect depends on the layout manager:

        - FlowLayoutManager: Arranges objects by signal flow topology
        - GridLayoutManager: Clusters connected objects together
        - Other managers: May have limited or no effect

        This method should be called after all objects and connections
        have been added to the patch.
        """
        if hasattr(self._layout_mgr, "optimize_layout"):
            self._layout_mgr.optimize_layout()

        # Process pending comments after layout optimization
        self._process_pending_comments()

    def _get_object_name(self, obj: AbstractBox) -> str:
        """Get the actual object name for validation purposes.

        For 'newobj' maxclass objects, extract the first word from the text field.
        For other objects, use the maxclass directly.
        """
        if obj.maxclass == "newobj":
            # Text is stored in _kwds for Box objects
            text = obj._kwds.get("text", "")
            if text:
                # Extract the first word from text (the object name)
                return text.split()[0] if text.split() else obj.maxclass
        return obj.maxclass

    def add_box(
        self,
        box: "Box",
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
    ) -> "Box":
        """registers the box and adds it to the patcher"""

        assert box.id, f"object {box} must have an id"
        self._node_ids.append(box.id)
        self._objects[box.id] = box
        self._boxes.append(box)
        if comment:
            self.add_associated_comment(box, comment, comment_pos)
        return box

    def add_associated_comment(
        self, box: "Box", comment: str, comment_pos: Optional[str] = None
    ):
        """Store a comment association to be processed later during layout optimization or save.

        This defers the actual comment positioning until after layout optimization,
        ensuring comments stay properly positioned relative to their associated boxes.
        """

        if comment_pos:
            assert comment_pos in [
                "above",
                "below",
                "right",
                "left",
            ], f"comment:{comment} / comment_pos: {comment_pos}"

        # Store the association for deferred processing
        if box.id is None:
            raise AssertionError("associated comment requires box with id")
        self._pending_comments.append((box.id, comment, comment_pos))

    def _process_pending_comments(self):
        """Process all pending comment associations and position comments relative to their boxes.

        This method is called during layout optimization and save operations to ensure
        comments are positioned correctly after any layout changes.
        """
        for box_id, comment_text, comment_pos in self._pending_comments:
            if box_id not in self._objects:
                continue  # Skip if box was removed

            box = self._objects[box_id]
            rect = box.patching_rect
            x, y, w, h = rect

            # Adjust rect height if needed
            if h != self._layout_mgr.box_height:
                if box.maxclass in maxref.MAXCLASS_DEFAULTS:
                    dh: float = 0.0
                    _, _, _, dh = maxref.MAXCLASS_DEFAULTS[box.maxclass][
                        "patching_rect"
                    ]
                    rect = Rect(x, y, w, dh)
                else:
                    h = self._layout_mgr.box_height
                    rect = Rect(x, y, w, h)

            # Calculate comment position
            if comment_pos:
                patching_rect = getattr(self._layout_mgr, comment_pos)(rect)
            else:
                patching_rect = self._layout_mgr.above(rect)

            # Create the comment with appropriate justification
            if comment_pos == "left":  # special case
                self.add_comment(comment_text, patching_rect, justify="right")
            else:
                self.add_comment(comment_text, patching_rect)

        # Clear pending comments after processing
        self._pending_comments.clear()

    def add_patchline_by_index(
        self, src_id: str, dst_id: str, dst_inlet: int = 0, src_outlet: int = 0
    ) -> "Patchline":
        """Patchline creation between two objects using stored indexes"""

        src = self._objects[src_id]
        dst = self._objects[dst_id]
        assert src.id and dst.id, f"object {src} and {dst} require ids"
        return self.add_patchline(src.id, src_outlet, dst.id, dst_inlet)

    def add_patchline(
        self, src_id: str, src_outlet: int, dst_id: str, dst_inlet: int
    ) -> "Patchline":
        """Primary patchline creation method with validation and logging.

        Args:
            src_id: Source object ID.
            src_outlet: Source outlet index.
            dst_id: Destination object ID.
            dst_inlet: Destination inlet index.

        Returns:
            Created Patchline object.

        Raises:
            InvalidConnectionError: If connection validation fails.
        """
        logger.debug(
            f"Adding patchline: {src_id}[{src_outlet}] -> {dst_id}[{dst_inlet}]"
        )

        # Validate connection if validation is enabled
        if self._validate_connections:
            src_obj = self._objects.get(src_id)
            dst_obj = self._objects.get(dst_id)

            if not src_obj:
                raise InvalidConnectionError(
                    f"Source object not found: {src_id}",
                    src=src_id,
                    dst=dst_id,
                    outlet=src_outlet,
                    inlet=dst_inlet,
                )

            if not dst_obj:
                raise InvalidConnectionError(
                    f"Destination object not found: {dst_id}",
                    src=src_id,
                    dst=dst_id,
                    outlet=src_outlet,
                    inlet=dst_inlet,
                )

            # Get the actual object names for validation
            src_name = self._get_object_name(src_obj)
            dst_name = self._get_object_name(dst_obj)

            is_valid, error_msg = maxref.validate_connection(
                src_name, src_outlet, dst_name, dst_inlet
            )
            if not is_valid:
                logger.warning(
                    f"Connection validation failed: {src_name}[{src_outlet}] -> {dst_name}[{dst_inlet}]: {error_msg}"
                )
                raise InvalidConnectionError(
                    f"Invalid connection from {src_name}[{src_outlet}] to {dst_name}[{dst_inlet}]: {error_msg}",
                    src=src_id,
                    dst=dst_id,
                    outlet=src_outlet,
                    inlet=dst_inlet,
                )

        # get order of lines between same pair of objects
        if (src_id, dst_id) == self._last_link:
            self._link_counter += 1
        else:
            self._link_counter = 0
            self._last_link = (src_id, dst_id)

        order = self._link_counter
        src, dst = [src_id, src_outlet], [dst_id, dst_inlet]
        patchline = Patchline(source=src, destination=dst, order=order)
        self._lines.append(patchline)
        self._edge_ids.append((src_id, dst_id))

        logger.debug(
            f"Created patchline (order={order}): {src_id}[{src_outlet}] -> {dst_id}[{dst_inlet}]"
        )
        return patchline

    def add_line(
        self, src_obj: "Box", dst_obj: "Box", inlet: int = 0, outlet: int = 0
    ) -> "Patchline":
        """Create a connection between two objects.

        Connects an outlet of the source object to an inlet of the destination
        object. Validates the connection if validation is enabled.

        Args:
            src_obj: Source object to connect from.
            dst_obj: Destination object to connect to.
            inlet: Destination inlet index (default: 0).
            outlet: Source outlet index (default: 0).

        Returns:
            The created Patchline object.

        Raises:
            InvalidConnectionError: If connection validation fails.

        Example:
            >>> osc = p.add_textbox('cycle~ 440')
            >>> gain = p.add_textbox('gain~')
            >>> p.add_line(osc, gain)  # Connect outlet 0 to inlet 0
        """
        assert src_obj.id and dst_obj.id, f"objects {src_obj} and {dst_obj} require ids"
        return self.add_patchline(src_obj.id, outlet, dst_obj.id, inlet)

    # alias for add_line
    link = add_line

    def add_textbox(
        self,
        text: str,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[List[str]] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds,
    ) -> "Box":
        """Add a text-based Max object to the patch.

        Creates a Max object from a text specification (e.g., 'cycle~ 440').
        Automatically looks up default attributes and applies appropriate
        maxclass based on the object type.

        Args:
            text: Max object specification (e.g., 'cycle~ 440', 'gain~').
            maxclass: Override the automatically determined maxclass.
            numinlets: Number of input connections.
            numoutlets: Number of output connections.
            outlettype: Types of outputs (e.g., ['signal', 'int']).
            patching_rect: Position and size rectangle.
            id: Unique identifier for the object.
            comment: Optional comment text.
            comment_pos: Comment position ('above', 'below', etc.).
            **kwds: Additional Max object properties.

        Returns:
            The created Box object.

        Example:
            >>> osc = p.add_textbox('cycle~ 440')
            >>> gain = p.add_textbox('gain~')
            >>> metro = p.add_textbox('metro 500')
        """
        _maxclass, *tail = text.split()

        defaults = maxref.MAXCLASS_DEFAULTS.get(_maxclass)

        if defaults:
            if maxclass is None and defaults.get("maxclass"):
                maxclass = defaults["maxclass"]

            if numinlets is None and "numinlets" in defaults:
                numinlets = defaults["numinlets"]

            if numoutlets is None and "numoutlets" in defaults:
                numoutlets = defaults["numoutlets"]

            if outlettype is None and "outlettype" in defaults:
                outlettype = defaults["outlettype"]

        kwds = self._textbox_helper(_maxclass, kwds)

        layout_rect = self.get_pos(maxclass) if maxclass else self.get_pos()
        if patching_rect is None and defaults and defaults.get("patching_rect"):
            default_rect = defaults["patching_rect"]
            patching_rect = Rect(
                layout_rect.x, layout_rect.y, default_rect.w, default_rect.h
            )
        elif patching_rect is None:
            patching_rect = layout_rect

        return self.add_box(
            Box(
                id=id or self.get_id(_maxclass),
                text=text,
                maxclass=maxclass or "newobj",
                numinlets=numinlets if numinlets is not None else 1,
                numoutlets=numoutlets if numoutlets is not None else 0,
                outlettype=outlettype if outlettype is not None else [""],
                patching_rect=patching_rect,
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def _textbox_helper(self, maxclass, kwds: dict) -> dict:
        """adds special case support for textbox"""
        if self.classnamespace == "rnbo":
            kwds["rnbo_classname"] = maxclass
            if maxclass in ["codebox", "codebox~"]:
                if "code" in kwds and "rnbo_extra_attributes" not in kwds:
                    if "\r" not in kwds["code"]:
                        kwds["code"] = kwds["code"].replace("\n", "\r\n")
                    kwds["rnbo_extra_attributes"] = dict(
                        code=kwds["code"],
                        hot=0,
                    )
        return kwds

    def _add_float(self, value, *args, **kwds) -> "Box":
        """type-handler for float values in `add`"""

        assert isinstance(value, float)
        name = None
        if args:
            name = args[0]
        elif "name" in kwds:
            name = kwds.get("name")
        else:
            return self.add_floatparam(longname="", initial=value, **kwds)

        if isinstance(name, str):
            return self.add_floatparam(longname=name, initial=value, **kwds)
        raise ValueError(
            "should be: .add(<float>, '<name>') OR .add(<float>, name='<name>')"
        )

    def _add_int(self, value, *args, **kwds) -> "Box":
        """type-handler for int values in `add`"""

        assert isinstance(value, int)
        name = None
        if args:
            name = args[0]
        elif "name" in kwds:
            name = kwds.get("name")
        else:
            return self.add_intparam(longname="", initial=value, **kwds)

        if isinstance(name, str):
            return self.add_intparam(longname=name, initial=value, **kwds)
        raise ValueError(
            "should be: .add(<int>, '<name>') OR .add(<int>, name='<name>')"
        )

    def _add_str(self, value, *args, **kwds) -> "Box":
        """type-handler for str values in `add`"""

        assert isinstance(value, str)

        maxclass, *text = value.split()
        txt = " ".join(text)

        # first check _maxclass_methods
        # these methods don't need the maxclass, just the `text` tail of value
        if maxclass in self._maxclass_methods:
            return self._maxclass_methods[maxclass](txt, **kwds)  # type: ignore
        # next two require value as a whole
        if maxclass == "p":
            return self.add_subpatcher(value, **kwds)
        if maxclass == "gen~":
            return self.add_gen_tilde(**kwds)
        if maxclass == "rnbo~":
            return self.add_rnbo(value, **kwds)
        return self.add_textbox(text=value, **kwds)

    def add(self, value, *args, **kwds) -> "Box":
        """generic adder: value can be a number or a list or text for an object."""

        if isinstance(value, float):
            return self._add_float(value, *args, **kwds)

        if isinstance(value, int):
            return self._add_int(value, *args, **kwds)

        if isinstance(value, str):
            return self._add_str(value, *args, **kwds)

        raise NotImplementedError

    def add_codebox(
        self,
        code: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        tilde=False,
        **kwds,
    ) -> "Box":
        """Add a codebox."""

        _maxclass = "codebox~" if tilde else "codebox"
        if "\r" not in code:
            code = code.replace("\n", "\r\n")

        if self.classnamespace == "rnbo":
            kwds["rnbo_classname"] = _maxclass
            if "rnbo_extra_attributes" not in kwds:
                kwds["rnbo_extra_attributes"] = dict(
                    code=code,
                    hot=0,
                )

        return self.add_box(
            Box(
                id=id or self.get_id(_maxclass),
                code=code,
                maxclass=_maxclass,
                outlettype=[""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_codebox_tilde(
        self,
        code: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds,
    ) -> "Box":
        """Add a codebox_tilde"""
        return self.add_codebox(
            code, patching_rect, id, comment, comment_pos, tilde=True, **kwds
        )

    def add_message(
        self,
        text: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds,
    ) -> "Box":
        """Add a max message."""

        return self.add_box(
            Box(
                id=id or self.get_id("message"),
                text=text or "",
                maxclass="message",
                numinlets=2,
                numoutlets=1,
                outlettype=[""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_comment(
        self,
        text: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        justify: Optional[str] = None,
        **kwds,
    ) -> "Box":
        """Add a basic comment object."""
        if justify:
            kwds["textjustification"] = {"left": 0, "center": 1, "right": 2}[justify]
        return self.add_box(
            Box(
                id=id or self.get_id("comment"),
                text=text,
                maxclass="comment",
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            )
        )

    def add_intbox(
        self,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds,
    ) -> "Box":
        """Add an int box object."""

        return self.add_box(
            Box(
                id=id or self.get_id("number"),
                maxclass="number",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    # alias
    add_int = add_intbox

    def add_floatbox(
        self,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds,
    ) -> "Box":
        """Add an float box object."""

        return self.add_box(
            Box(
                id=id or self.get_id("flonum"),
                maxclass="flonum",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    # alias
    add_float = add_floatbox

    def add_floatparam(
        self,
        longname: str,
        initial: Optional[float] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        shortname: Optional[str] = None,
        id: Optional[str] = None,
        rect: Optional[Rect] = None,
        hint: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds,
    ) -> "Box":
        """Add a float parameter object."""

        return self.add_box(
            Box(
                id=id or self.get_id("flonum"),
                maxclass="flonum",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                parameter_enable=1,
                saved_attribute_attributes=dict(
                    valueof=dict(
                        parameter_initial=[initial or 0.5],
                        parameter_initial_enable=1,
                        parameter_longname=longname,
                        # parameter_mmax=maximum,
                        parameter_shortname=shortname or "",
                        parameter_type=0,
                    )
                ),
                maximum=maximum,
                minimum=minimum,
                patching_rect=rect or self.get_pos(),
                hint=hint or (longname if self._auto_hints else ""),
                **kwds,
            ),
            comment or longname,  # units can also be added here
            comment_pos,
        )

    def add_intparam(
        self,
        longname: str,
        initial: Optional[int] = None,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
        shortname: Optional[str] = None,
        id: Optional[str] = None,
        rect: Optional[Rect] = None,
        hint: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds,
    ) -> "Box":
        """Add an int parameter object."""

        return self.add_box(
            Box(
                id=id or self.get_id("number"),
                maxclass="number",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                parameter_enable=1,
                saved_attribute_attributes=dict(
                    valueof=dict(
                        parameter_initial=[initial or 1],
                        parameter_initial_enable=1,
                        parameter_longname=longname,
                        parameter_mmax=maximum,
                        parameter_shortname=shortname or "",
                        parameter_type=1,
                    )
                ),
                maximum=maximum,
                minimum=minimum,
                patching_rect=rect or self.get_pos(),
                hint=hint or (longname if self._auto_hints else ""),
                **kwds,
            ),
            comment or longname,  # units can also be added here
            comment_pos,
        )

    def add_attr(
        self,
        name: str,
        value: float,
        shortname: Optional[str] = None,
        id: Optional[str] = None,
        rect: Optional[Rect] = None,
        hint: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        autovar=True,
        show_label=False,
        **kwds,
    ) -> "Box":
        """create a param-linke attrui entry"""
        if autovar:
            kwds["varname"] = name

        return self.add_box(
            Box(
                id=id or self.get_id("attrui"),
                text="attrui",
                maxclass="attrui",
                attr=name,
                parameter_enable=1,
                attr_display=show_label,
                saved_attribute_attributes=dict(
                    valueof=dict(
                        parameter_initial=[name, value],
                        parameter_initial_enable=1,
                        parameter_longname=name,
                        parameter_shortname=shortname or "",
                    )
                ),
                patching_rect=rect or self.get_pos(),
                hint=name if self._auto_hints else hint or "",
                **kwds,
            ),
            comment or name,  # units can also be added here
            comment_pos,
        )

    def add_subpatcher(
        self,
        text: str,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[List[str]] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        patcher: Optional["Patcher"] = None,
        **kwds,
    ) -> "Box":
        """Add a subpatcher object."""

        # For subpatchers, use the text (e.g., "p subpatch") for semantic ID
        obj_name = text.split()[0] if text else "newobj"
        return self.add_box(
            Box(
                id=id or self.get_id(obj_name),
                text=text,
                maxclass=maxclass or "newobj",
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 0,
                outlettype=outlettype or [""],
                patching_rect=patching_rect or self.get_pos(),
                patcher=patcher or Patcher(parent=self),
                **kwds,
            )
        )

    def add_gen(self, text: Optional[str] = None, tilde=False, **kwds):
        """Add a gen object."""
        prefix = "gen~" if tilde else "gen"
        _text = f"{prefix} {text}" if text else prefix
        return self.add_subpatcher(
            _text, patcher=Patcher(parent=self, classnamespace="dsp.gen"), **kwds
        )

    def add_gen_tilde(self, text: Optional[str] = None, **kwds):
        """Add a gen~ object."""
        return self.add_gen(text=text, tilde=True, **kwds)

    def add_rnbo(self, text: str = "rnbo~", **kwds):
        """Add an rnbo~ object."""
        if "inletInfo" not in kwds:
            if "numinlets" in kwds:
                inletInfo: dict[str, list] = {"IOInfo": []}
                for i in range(kwds["numinlets"]):
                    inletInfo["IOInfo"].append(
                        dict(comment="", index=i + 1, tag=f"in{i + 1}", type="signal")
                    )
                kwds["inletInfo"] = inletInfo
        if "outletInfo" not in kwds:
            if "numoutlets" in kwds:
                outletInfo: dict[str, list] = {"IOInfo": []}
                for i in range(kwds["numoutlets"]):
                    outletInfo["IOInfo"].append(
                        dict(comment="", index=i + 1, tag=f"out{i + 1}", type="signal")
                    )
                kwds["outletInfo"] = outletInfo

        return self.add_subpatcher(
            text, patcher=Patcher(parent=self, classnamespace="rnbo"), **kwds
        )

    def add_coll(
        self,
        name: Optional[str] = None,
        dictionary: Optional[dict] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds,
    ):
        """Add a coll object with option to pre-populate from a py dictionary."""
        extra = {"saved_object_attributes": {"embed": embed, "precision": 6}}
        if dictionary:
            extra["coll_data"] = {  # type: ignore
                "count": len(dictionary.keys()),
                "data": [{"key": k, "value": v} for k, v in dictionary.items()],  # type: ignore
            }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id("coll"),
                text=text or f"coll {name} @embed {embed}"
                if name
                else f"coll @embed {embed}",
                maxclass="newobj",
                numinlets=1,
                numoutlets=4,
                outlettype=["", "", "", ""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_dict(
        self,
        name: Optional[str] = None,
        dictionary: Optional[dict] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds,
    ):
        """Add a dict object with option to pre-populate from a py dictionary."""
        extra = {
            "saved_object_attributes": {
                "embed": embed,
                "parameter_enable": kwds.get("parameter_enable", 0),
                "parameter_mappable": kwds.get("parameter_mappable", 0),
            },
            "data": dictionary or {},
        }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id("dict"),
                text=text or f"dict {name} @embed {embed}"
                if name
                else f"dict @embed {embed}",
                maxclass="newobj",
                numinlets=2,
                numoutlets=4,
                outlettype=["dictionary", "", "", ""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_table(
        self,
        name: Optional[str] = None,
        array: Optional[List[Union[int, float]]] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        tilde=False,
        **kwds,
    ):
        """Add a table object with option to pre-populate from a py list."""

        extra = {
            "embed": embed,
            "saved_object_attributes": {
                "name": name,
                "parameter_enable": kwds.get("parameter_enable", 0),
                "parameter_mappable": kwds.get("parameter_mappable", 0),
                "range": kwds.get("range", 128),
                "showeditor": 0,
                "size": len(array) if array else 128,
            },
            # "showeditor": 0,
            # 'size': kwds.get('size', 128),
            "table_data": array or [],
            "editor_rect": [100.0, 100.0, 300.0, 300.0],
        }
        kwds.update(extra)
        table_type = "table~" if tilde else "table"
        return self.add_box(
            Box(
                id=id or self.get_id(table_type),
                text=text or f"{table_type} {name} @embed {embed}"
                if name
                else f"{table_type} @embed {embed}",
                maxclass="newobj",
                numinlets=2,
                numoutlets=2,
                outlettype=["int", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_table_tilde(
        self,
        name: Optional[str] = None,
        array: Optional[List[Union[int, float]]] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds,
    ):
        """Add a table~ object with option to pre-populate from a py list."""

        return self.add_table(
            name,
            array,
            embed,
            patching_rect,
            text,
            id,
            comment,
            comment_pos,
            tilde=True,
            **kwds,
        )

    def add_itable(
        self,
        name: Optional[str] = None,
        array: Optional[List[Union[int, float]]] = None,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds,
    ):
        """Add a itable object with option to pre-populate from a py list."""

        extra = {
            "range": kwds.get("range", 128),
            "size": len(array) if array else 128,
            "table_data": array or [],
        }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id("itable"),
                text=text or f"itable {name}",
                maxclass="itable",
                numinlets=2,
                numoutlets=2,
                outlettype=["int", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_umenu(
        self,
        prefix: Optional[str] = None,
        autopopulate: int = 1,
        items: Optional[List[str]] = None,
        patching_rect: Optional[Rect] = None,
        depth: Optional[int] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds,
    ):
        """Add a umenu object with option to pre-populate items from a py list."""

        # interleave commas in a list
        def _commas(xs):
            return [i for pair in zip(xs, [","] * len(xs)) for i in pair]

        return self.add_box(
            Box(
                id=id or self.get_id("umenu"),
                maxclass="umenu",
                numinlets=1,
                numoutlets=3,
                outlettype=["int", "", ""],
                autopopulate=autopopulate or 1,
                depth=depth or 1,
                items=_commas(items) or [],
                prefix=prefix or "",
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_bpatcher(
        self,
        name: str,
        numinlets: int = 1,
        numoutlets: int = 1,
        outlettype: Optional[List[str]] = None,
        bgmode: int = 0,
        border: int = 0,
        clickthrough: int = 0,
        enablehscroll: int = 0,
        enablevscroll: int = 0,
        lockeddragscroll: int = 0,
        offset: Optional[List[float]] = None,
        viewvisibility: int = 1,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds,
    ):
        """Add a bpatcher object -- name or patch of bpatcher .maxpat is required."""

        return self.add_box(
            Box(
                id=id or self.get_id("bpatcher"),
                name=name,
                maxclass="bpatcher",
                numinlets=numinlets,
                numoutlets=numoutlets,
                bgmode=bgmode,
                border=border,
                clickthrough=clickthrough,
                enablehscroll=enablehscroll,
                enablevscroll=enablevscroll,
                lockeddragscroll=lockeddragscroll,
                viewvisibility=viewvisibility,
                outlettype=outlettype or ["float", "", ""],
                patching_rect=patching_rect or self.get_pos(),
                offset=offset or [0.0, 0.0],
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_beap(self, name: str, **kwds):
        """Add a beap bpatcher object."""

        _varname = name if ".maxpat" not in name else name.rstrip(".maxpat")
        return self.add_bpatcher(name=name, varname=_varname, extract=1, **kwds)
