"""Core classes for py2max: Patcher, Box, and Patchline.

This module contains the main classes for creating and managing Max/MSP patches:

- Patcher: Core class for creating and managing Max patches
- Box: Represents individual Max objects
- Patchline: Represents connections between objects
- InvalidConnectionError: Exception for invalid connections

The Patcher class provides methods for adding various Max objects and connecting
them together, with automatic layout management and connection validation.

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
from typing import Optional, Union, Tuple, List, cast

from . import abstract
from . import layout
from . import maxref
from .common import Rect


# ---------------------------------------------------------------------------
# CONSTANTS

MAX_VER_MAJOR = 8
MAX_VER_MINOR = 5
MAX_VER_REVISION = 5

# ---------------------------------------------------------------------------
# Exceptions


class InvalidConnectionError(Exception):
    """Raised when attempting to create an invalid patchline connection.

    This exception is raised when validation is enabled and an invalid
    connection is attempted, such as connecting to a non-existent inlet
    or outlet.
    """


# ---------------------------------------------------------------------------
# Utility Classes and functions


# ---------------------------------------------------------------------------
# Primary Classes


class Patcher(abstract.AbstractPatcher):
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
        layout: Layout manager type ('horizontal', 'vertical', 'grid', 'flow', 'columnar', 'matrix').
        auto_hints: Whether to automatically generate object hints.
        openinpresentation: Presentation mode setting.
        validate_connections: Whether to validate patchline connections.
        flow_direction: Direction for flow-based layouts ('horizontal', 'vertical').
        cluster_connected: Whether to cluster connected objects in grid layout.
        num_dimensions: Number of columns (columnar) or rows (matrix) for matrix/columnar layouts.
        dimension_spacing: Spacing between columns/rows for matrix/columnar layouts.

    Example:
        >>> p = Patcher('my-patch.maxpat', layout='grid')
        >>> osc = p.add_textbox('cycle~ 440')
        >>> gain = p.add_textbox('gain~')
        >>> p.add_line(osc, gain)
        >>> p.save()
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
        # New matrix/columnar layout parameters
        num_dimensions: int = 4,
        dimension_spacing: float = 100.0,
    ):
        self._path = path
        self._parent = parent
        self._node_ids: list[str] = []  # ids by order of creation
        self._objects: dict[str, abstract.AbstractBox] = {}  # dict of objects by id
        self._boxes: list[
            abstract.AbstractBox
        ] = []  # store child objects (boxes, etc.)
        self._lines: list[abstract.AbstractPatchline] = []  # store patchline objects
        self._edge_ids: list[
            tuple[str, str]
        ] = []  # store edge-ids by order of creation
        self._id_counter = 0
        self._link_counter = 0
        self._last_link: Optional[tuple[str, str]] = None
        self._reset_on_render = reset_on_render
        self._flow_direction = flow_direction
        self._cluster_connected = cluster_connected
        self._num_dimensions = num_dimensions
        self._dimension_spacing = dimension_spacing
        self._layout_mgr: abstract.AbstractLayoutManager = self.set_layout_mgr(layout)
        self._auto_hints = auto_hints
        self._validate_connections = validate_connections
        self._pending_comments: list[tuple[str, str, Optional[str]]] = []  # [(box_id, comment_text, comment_pos), ...]
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
        """Save the patch to a specified file path.

        Renders all objects and connections, then saves the patch as a
        .maxpat JSON file that can be opened in Max/MSP.

        Args:
            path: File path where the patch should be saved.
        """
        path = Path(path)
        if path.parent:
            path.parent.mkdir(exist_ok=True)
        self.render()
        with open(path, "w", encoding="utf8") as f:
            json.dump(self.to_dict(), f, indent=4)

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

    def get_id(self) -> str:
        """helper func to increment object ids"""
        self._id_counter += 1
        return f"obj-{self._id_counter}"

    def set_layout_mgr(self, name: str) -> layout.LayoutManager:
        """takes a name and returns an instance of a layout manager"""
        if name == "horizontal":
            return layout.HorizontalLayoutManager(self)
        elif name == "vertical":
            return layout.VerticalLayoutManager(self)            
        elif name == "flow":
            return layout.FlowLayoutManager(self, flow_direction=self._flow_direction)
        elif name == "grid":
            return layout.GridLayoutManager(
                self,
                flow_direction=self._flow_direction,
                cluster_connected=self._cluster_connected,
            )
        elif name == "matrix":
            return layout.MatrixLayoutManager(
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

    def _get_object_name(self, obj: abstract.AbstractBox) -> str:
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
                    _, _, _, dh = maxref.MAXCLASS_DEFAULTS[box.maxclass]["patching_rect"]
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
        """primary patchline creation method"""

        # Validate connection if validation is enabled
        if self._validate_connections:
            src_obj = self._objects.get(src_id)
            dst_obj = self._objects.get(dst_id)

            if src_obj and dst_obj:
                # Get the actual object names for validation
                src_name = self._get_object_name(src_obj)
                dst_name = self._get_object_name(dst_obj)

                is_valid, error_msg = maxref.validate_connection(
                    src_name, src_outlet, dst_name, dst_inlet
                )
                if not is_valid:
                    raise InvalidConnectionError(
                        f"Invalid connection from {src_name}[{src_outlet}] to {dst_name}[{dst_inlet}]: {error_msg}"
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
            patching_rect = Rect(layout_rect.x, layout_rect.y, default_rect.w, default_rect.h)
        elif patching_rect is None:
            patching_rect = layout_rect

        return self.add_box(
            Box(
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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

        return self.add_box(
            Box(
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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
                id=id or self.get_id(),
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


class Box(abstract.AbstractBox):
    """Represents a Max object in a patch.

    The Box class encapsulates a single Max object with its properties,
    position, and connections. It provides methods for introspection
    and help information.

    Args:
        maxclass: Max object class name (e.g., 'newobj', 'flonum').
        numinlets: Number of input connections.
        numoutlets: Number of output connections.
        id: Unique identifier for the object.
        patching_rect: Position and size rectangle.
        **kwds: Additional Max object properties.

    Attributes:
        id: Unique identifier for the object.
        maxclass: Max object class name.
        numinlets: Number of input connections.
        numoutlets: Number of output connections.
        patching_rect: Position and size as Rect.
    """

    def __init__(
        self,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        id: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        **kwds,
    ):
        self.id = id
        self.maxclass = maxclass or "newobj"
        self.numinlets = numinlets or 0
        self.numoutlets = numoutlets or 1
        # self.outlettype = outlettype
        self.patching_rect = patching_rect or Rect(0, 0, 62, 22)

        self._kwds = self._remove_none_entries(kwds)
        self._patcher = self._kwds.pop("patcher", None)

    def _remove_none_entries(self, kwds):
        """removes items in the dict which have None values.

        TODO: make recursive in case of nested dicts.
        """
        return {k: v for k, v in kwds.items() if v is not None}

    def __iter__(self):
        yield self
        if self._patcher:
            yield from iter(self._patcher)

    def __repr__(self):
        return f"{self.__class__.__name__}(id='{self.id}', maxclass='{self.maxclass}')"

    def render(self):
        """convert self and children to dictionary."""
        if self._patcher:
            self._patcher.render()
            self.patcher = self._patcher.to_dict()

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        d.update(self._kwds)
        return dict(box=d)

    @classmethod
    def from_dict(cls, obj_dict):
        """create instance from dict"""
        box = cls()
        box.__dict__.update(obj_dict)
        if hasattr(box, "patcher"):
            box._patcher = Patcher.from_dict(getattr(box, "patcher"))
        return box

    @property
    def oid(self) -> Optional[int]:
        """numerical part of object id as int"""
        if self.id:
            return int(self.id[4:])
        return None

    @property
    def subpatcher(self):
        """synonym for parent patcher object"""
        return self._patcher

    @property
    def text(self):
        """Get the text content of the box."""
        # Check if text is stored as a direct attribute (from file loading)
        if 'text' in self.__dict__:
            return self.__dict__['text']
        # Otherwise get from _kwds (from programmatic creation)
        return self._kwds.get("text", "")

    def help_text(self) -> str:
        """Get formatted help documentation for this Max object.

        Returns:
            Formatted help string with object documentation from .maxref.xml files.
        """
        return maxref.get_object_help(self.maxclass)

    def help(self) -> None:
        """Print formatted help documentation for this Max object."""
        print(self.help_text())

    def get_info(self) -> Optional[dict]:
        """Get complete object information from .maxref.xml files.

        Returns:
            Dictionary with complete object information or None if not found.
        """
        return maxref.get_object_info(self.maxclass)

    def get_inlet_count(self) -> Optional[int]:
        """Get the number of inlets for this object from maxref data.

        Returns:
            Number of inlets or None if unknown.
        """
        from .maxref import get_inlet_count

        object_name = self._get_object_name()
        return get_inlet_count(object_name)

    def get_outlet_count(self) -> Optional[int]:
        """Get the number of outlets for this object from maxref data.

        Returns:
            Number of outlets or None if unknown.
        """
        from .maxref import get_outlet_count

        object_name = self._get_object_name()
        return get_outlet_count(object_name)

    def get_inlet_types(self) -> List[str]:
        """Get the inlet types for this object from maxref data

        Returns:
            List of inlet type strings
        """
        from .maxref import get_inlet_types

        object_name = self._get_object_name()
        return get_inlet_types(object_name)

    def get_outlet_types(self) -> List[str]:
        """Get the outlet types for this object from maxref data

        Returns:
            List of outlet type strings
        """
        from .maxref import get_outlet_types

        object_name = self._get_object_name()
        return get_outlet_types(object_name)

    def _get_object_name(self) -> str:
        """Get the actual object name for this Box.

        For 'newobj' maxclass objects, extract the first word from the text field.
        For other objects, use the maxclass directly.
        """
        if self.maxclass == "newobj":
            # Text is stored in _kwds for Box objects
            text = self._kwds.get("text", "")
            if text:
                # Extract the first word from text (the object name)
                return text.split()[0] if text.split() else self.maxclass
        return self.maxclass


class Patchline(abstract.AbstractPatchline):
    """Represents a connection between two Max objects.

    A Patchline connects an outlet of one object to an inlet of another,
    enabling signal or message flow between objects in a patch.

    Args:
        source: Source connection as [object_id, outlet_index].
        destination: Destination connection as [object_id, inlet_index].
        **kwds: Additional patchline properties.

    Attributes:
        source: Source object ID and outlet index.
        destination: Destination object ID and inlet index.
    """

    def __init__(
        self, source: Optional[list] = None, destination: Optional[list] = None, **kwds
    ):
        self.source = source or []
        self.destination = destination or []
        self._kwds = kwds

    def __repr__(self):
        return f"Patchline({self.source} -> {self.destination})"

    @property
    def src(self):
        """first object from source list"""
        return self.source[0]

    @property
    def dst(self):
        """first object from destination list"""
        return self.destination[0]

    def to_tuple(self) -> Tuple[str, str, str, str, Union[str, int]]:
        """Return a tuple describing the patchline."""
        return (
            self.source[0],
            self.source[1],
            self.destination[0],
            self.destination[1],
            self._kwds.get("order", 0),
        )

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        d.update(self._kwds)
        return dict(patchline=d)

    @classmethod
    def from_dict(cls, obj_dict: dict):
        """convert to`Patchline` object from dict"""
        patchline = cls()
        patchline.__dict__.update(obj_dict)
        return patchline
