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
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union, cast

from py2max import layout as layout_module
from py2max.log import get_logger

from .abstract import (
    AbstractBox,
    AbstractLayoutManager,
    AbstractPatcher,
    AbstractPatchline,
)
from .box import Box
from .common import Rect
from .factory import BoxFactoryMixin
from .patchline import Patchline
from .serialization import SerializationMixin

# ---------------------------------------------------------------------------
# CONSTANTS

MAX_VER_MAJOR = 8
MAX_VER_MINOR = 5
MAX_VER_REVISION = 5

# Module logger
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Primary Classes


class Patcher(BoxFactoryMixin, SerializationMixin, AbstractPatcher):
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
        parent: Optional["AbstractPatcher"] = None,
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
        device_type: str = "audio_effect",
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
        self._edge_ids: list[
            tuple[str, str]
        ] = []  # store edge-ids by order of creation
        self._id_counter = 0
        self._link_counter = 0
        self._last_link: Optional[tuple[str, str]] = None
        self._reset_on_render = reset_on_render
        self._semantic_ids = semantic_ids
        self._semantic_counters: dict[str, int] = {}  # Track counts per object type
        self._device_type = device_type  # M4L device type for .amxd writes
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
        self.boxes: List[Dict[str, Any]] = []
        self.lines: List[Dict[str, Any]] = []
        # self.parameters: dict = {}
        self.dependency_cache: List[Any] = []
        self.autosave = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(path='{self._path}')"

    def __iter__(self) -> Iterator[Any]:
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
    def from_dict(
        cls, patcher_dict: Dict[str, Any], save_to: Optional[str] = None
    ) -> "Patcher":
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
        """create a patcher instance from a .maxpat or .amxd file"""

        path = Path(path)
        device_type: Optional[str] = None
        if path.suffix.lower() == ".amxd":
            # Lazy import: m4l is a feature layer, kept off core's import path.
            from py2max.m4l import unpack_amxd

            payload, device_type = unpack_amxd(path.read_bytes())
            maxpat = json.loads(payload)
        else:
            with open(path, encoding="utf8") as f:
                maxpat = json.load(f)
        patcher = Patcher.from_dict(maxpat["patcher"], save_to)
        if device_type is not None:
            patcher._device_type = device_type
        return patcher

    @staticmethod
    def _matches(box: AbstractBox, text: str) -> bool:
        """True if a box matches ``text`` by exact maxclass or text prefix.

        Shared predicate for the ``find*`` methods, which differ only in scope
        (recursive vs flat) and return shape, not in match semantics.
        """
        if box.maxclass == text:
            return True
        box_text = getattr(box, "text", "")
        return bool(box_text and box_text.startswith(text))

    def find(self, text: str) -> Optional["Box"]:
        """Find box object by maxclass or text pattern.

        Recursively searches through all objects in the patch (including
        subpatchers) to find one matching the specified maxclass or text prefix.

        Args:
            text: The maxclass name or text pattern to search for.

        Returns:
            The first matching Box object, or None if not found.
        """
        for obj in self:
            if not isinstance(obj, Patcher) and self._matches(obj, text):
                return cast("Box", obj)
        return None

    def find_box(self, text: str) -> Optional["Box"]:
        """Find a box in this patcher (non-recursive) by maxclass or text prefix.

        returns box if found else None
        """
        for box in self._objects.values():
            if self._matches(box, text):
                return cast("Box", box)
        return None

    def find_box_with_index(self, text: str) -> Optional[Tuple[int, "Box"]]:
        """Find a box and its index by maxclass or text prefix (non-recursive).

        returns (index, box) if found
        """
        for i, box in enumerate(self._boxes):
            if self._matches(box, text):
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

    def enable_presentation(self, devicewidth: Optional[int] = None) -> "Patcher":
        """Configure this patcher to open as a Max for Live device.

        Sets ``openinpresentation=1`` so Ableton Live renders the device
        strip instead of the patcher view, and optionally sets
        ``devicewidth``. Ableton's device strip height is fixed at ~170 px;
        only width is author-controlled.
        """
        from py2max.m4l import enable_presentation

        return enable_presentation(self, devicewidth=devicewidth)

    def enforce_integer_coords(self) -> int:
        """Round all rect coordinates in this patcher tree to integers.

        Ableton renders fractional device-strip coordinates blurry on
        non-retina displays. Returns the number of rects that were
        non-integer and got rounded. Recurses into subpatchers.
        """
        from py2max.m4l import enforce_integer_coords

        return enforce_integer_coords(self)

    def to_svg(
        self,
        output_path: Union[str, Path],
        show_ports: bool = True,
        title: Optional[str] = None,
    ) -> None:
        """Export this patcher to SVG format.

        Args:
            output_path: Output file path for the SVG.
            show_ports: Whether to show inlet/outlet ports on boxes.
            title: Optional title to display at top of SVG.

        Example:
            >>> p = Patcher('my-patch.maxpat')
            >>> osc = p.add_textbox('cycle~ 440')
            >>> dac = p.add_textbox('ezdac~')
            >>> p.add_line(osc, dac)
            >>> p.to_svg('/tmp/my-patch.svg')
        """
        from ..export.svg import export_svg

        export_svg(self, output_path, show_ports=show_ports, title=title)

    def to_svg_string(
        self,
        show_ports: bool = True,
        title: Optional[str] = None,
    ) -> str:
        """Export this patcher to SVG format as a string.

        Args:
            show_ports: Whether to show inlet/outlet ports on boxes.
            title: Optional title to display at top of SVG.

        Returns:
            SVG content as a string.

        Example:
            >>> p = Patcher('my-patch.maxpat')
            >>> osc = p.add_textbox('cycle~ 440')
            >>> svg_content = p.to_svg_string()
        """
        from ..export.svg import export_svg_string

        return export_svg_string(self, show_ports=show_ports, title=title)

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
            return layout_module.FlowLayoutManager(
                self, flow_direction=self._flow_direction
            )
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
