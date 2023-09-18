"""a sketch of an alternative design for py2max

Each object has:
    - an inner model dict
    - property-based access to that model dict
    - specialized classes to differentiate between Box Types

"""

"""py2max: a pure python library to generate .maxpat patcher files.

basic usage:

    >>> p = Patcher('out.maxpat')
    >>> osc1 = p.add_textbox('cycle~ 440')
    >>> gain = p.add_textbox('gain~')
    >>> dac = p.add_textbox('ezdac~')
    >>> p.add_line(osc1, gain)
    >>> p.add_line(gain, dac)
    >>> p.save()

"""
import abc
import json
from pathlib import Path
from typing import Optional, Union, Tuple, List

from .maxclassdb import MAXCLASS_DEFAULTS
from .common import Rect

# ---------------------------------------------------------------------------
# CONSTANTS

MAX_VER_MAJOR = 8
MAX_VER_MINOR = 5
MAX_VER_REVISION = 5

# ---------------------------------------------------------------------------
# Utility Classes and functions

# ---------------------------------------------------------------------------
# Layout Classes


class LayoutManager(abc.ABC):
    """Utility class to help with object layout.

    This is a basic horizontal layout manager.
    i.e. objects flow and wrap to the right.
    """

    DEFAULT_PAD = 1.5 * 32.0
    DEFAULT_BOX_WIDTH = 66.0
    DEFAULT_BOX_HEIGHT = 22.0
    DEFAULT_COMMENT_PAD = 2

    def __init__(
        self,
        parent: "Patcher",
        pad: Optional[int] = None,
        box_width: Optional[int] = None,
        box_height: Optional[int] = None,
        comment_pad: Optional[int] = None,
    ):
        self.parent = parent
        self.pad = pad or self.DEFAULT_PAD
        self.box_width = box_width or self.DEFAULT_BOX_WIDTH
        self.box_height = box_height or self.DEFAULT_BOX_HEIGHT
        self.comment_pad = comment_pad or self.DEFAULT_COMMENT_PAD
        self.x_layout_counter = 0
        self.y_layout_counter = 0
        self.prior_rect = None
        self.mclass_rect = None

    def get_rect_from_maxclass(self, maxclass: str) -> Optional[Rect]:
        """retrieves default patching_rect from defaults dictionary."""
        try:
            return MAXCLASS_DEFAULTS[maxclass]["patching_rect"]
        except KeyError:
            return None

    def get_absolute_pos(self, rect: Rect) -> Rect:
        """returns an absolute position for the object"""
        x, y, w, h = rect

        pad = self.pad

        if x > 0.5 * self.parent.width:
            x1 = x - (w + pad)
            x = x1 - (x1 - self.parent.width) if x1 > self.parent.width else x1
        else:
            x1 = x + pad

        y1 = y - (h + pad)
        y = y1 - (y1 - self.parent.height) if y1 > self.parent.height else y1

        return Rect(x, y, w, h)

    @abc.abstractmethod
    def get_relative_pos(self, rect: Rect) -> Rect:
        """returns a relative position for the object"""

    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """helper func providing very rough auto-layout of objects"""
        x = 0.0
        y = 0.0
        w = self.box_width  # 66.0
        h = self.box_height  # 22.0

        if maxclass:
            mclass_rect = self.get_rect_from_maxclass(maxclass)
            if mclass_rect and (mclass_rect.x or mclass_rect.y):
                if mclass_rect.x:
                    x = float(mclass_rect.x * self.parent.width)
                if mclass_rect.y:
                    y = float(mclass_rect.y * self.parent.height)

                _rect = Rect(x, y, mclass_rect.w, mclass_rect.h)
                return self.get_absolute_pos(_rect)

        _rect = Rect(x, y, w, h)
        return self.get_relative_pos(_rect)

    @property
    def patcher_rect(self) -> Rect:
        """return rect coordinates of the parent patcher"""
        return self.parent.rect

    def above(self, rect: Rect) -> Rect:
        """Return a position of a comment above the object"""
        x, y, w, h = rect
        return Rect(x, y - h, w, h)

    def below(self, rect: Rect) -> Rect:
        """Return a position of a comment below the object"""
        x, y, w, h = rect
        return Rect(x, y + h, w, h)

    def left(self, rect: Rect) -> Rect:
        """Return a position of a comment left of the object"""
        x, y, w, h = rect
        return Rect(x - (w + self.comment_pad), y, w, h)

    def right(self, rect: Rect) -> Rect:
        """Return a position of a comment right of the object"""
        x, y, w, h = rect
        return Rect(x + (w + self.comment_pad), y, w, h)


class HorizontalLayoutManager(LayoutManager):
    """Utility class to help with object layout.

    This is a basic horizontal layout manager.
    i.e. objects fill from left to right of the
    grid and and wrap horizontally.
    """

    def get_relative_pos(self, rect: Rect) -> Rect:
        """returns a relative horizontal position for the object"""
        x, y, w, h = rect

        pad = self.pad  # 32.0

        x_shift = 3 * pad * self.x_layout_counter
        y_shift = 1.5 * pad * self.y_layout_counter
        x = pad + x_shift

        self.x_layout_counter += 1
        if x + w + 2 * pad > self.parent.width:
            self.x_layout_counter = 0
            self.y_layout_counter += 1

        y = pad + y_shift

        return Rect(x, y, w, h)


class VerticalLayoutManager(LayoutManager):
    """Utility class to help with obadject layout.

    This is a basic vertical layout manager.
    i.e. objects fill from top to bottom of the
    grid and and wrap vertically.
    """

    def get_relative_pos(self, rect: Rect) -> Rect:
        """returns a relative vertical position for the object"""
        x, y, w, h = rect

        pad = self.pad  # 32.0

        x_shift = 3 * pad * self.x_layout_counter
        y_shift = 1.5 * pad * self.y_layout_counter
        y = pad + y_shift

        self.y_layout_counter += 1
        if y + h + 2 * pad > self.parent.height:
            self.x_layout_counter += 1
            self.y_layout_counter = 0

        x = pad + x_shift

        return Rect(x, y, w, h)


# ---------------------------------------------------------------------------
# Primary Classes

class Box:
    """Max Box object"""

    def __init__(
        self,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[list[str]] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds,
    ):
        self._model = {
            "id": id,
            "maxclass": maxclass or "newobj",
            "numinlets": numinlets or 0,
            "numoutlets": numoutlets or 1,
            "outlettype": outlettype or [""],
            "patching_rect": patching_rect or Rect(0, 0, 62, 22),
        }
        self._kwds = kwds
        self.patcher = None

    def __repr__(self):
        return f"{self.__class__.__name__}(id='{self.id}', maxclass='{self.maxclass}')"

    @classmethod
    def from_dict(cls, obj_dict):
        """create instance from dict"""
        box = cls()
        box._model.update(obj_dict)
        if "patcher" in box._model:
            box.patcher = Patcher.from_dict(box._model["patcher"])
        return box

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = self._model.copy()
        d.update(self._kwds)
        return dict(box=d)

    def render(self):
        """convert self and children to dictionary."""
        if self.patcher:
            self.patcher.render()
            self._model["patcher"] = self.patcher.to_dict()

    @property
    def id(self):
        return self._model["id"]

    @id.setter
    def id(self, value: str):
        self._model["id"] = value

    @property
    def maxclass(self):
        return self._model["maxclass"]

    @maxclass.setter
    def maxclass(self, value: str):
        self._model["maxclass"] = value

    @property
    def numinlets(self):
        return self._model["numinlets"]

    @numinlets.setter
    def numinlets(self, value: int):
        self._model["numinlets"] = value

    @property
    def numoutlets(self):
        return self._model["numoutlets"]

    @numoutlets.setter
    def numoutlets(self, value: int):
        self._model["numoutlets"] = value

    @property
    def outlettype(self):
        return self._model["outlettype"]

    @outlettype.setter
    def outlettype(self, value: list[str]):
        self._model["outlettype"] = value

    @property
    def oid(self) -> Optional[int]:
        """numerical part of object id as int"""
        if self.id:
            return int(self.id[4:])
        return None

    @property
    def subpatcher(self):
        """synonym for parent patcher object"""
        return self.patcher


class TextBox(Box):
    def __init__(
        self,
        text: str = "",
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[list[str]] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds,
    ):
        super().__init__(
            maxclass, numinlets, numoutlets, outlettype, patching_rect, id, **kwds
        )
        self.text = text

    @property
    def text(self):
        assert "text" in self._model, "`text` field must be in `model`"
        return self._model["text"]

    @text.setter
    def text(self, value: str):
        self._model["text"] = value


class Message(TextBox):
    def __init__(
        self,
        text: str = "",
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds,
    ):
        super().__init__(text, "message", 2, 1, None, patching_rect, id, **kwds)
        self.text = text


class IntBox(Box):
    def __init__(
        self,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds,
    ):
        super().__init__("number", 1, 2, ["", "bang"], patching_rect, id, **kwds)


class IntParam(IntBox):
    def __init__(
        self,
        longname: str,
        initial: Optional[int] = None,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
        shortname: Optional[str] = None,
        id: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        hint: Optional[str] = None,
        **kwds,
    ):
        """int parameter object."""
        super().__init__(patching_rect, id, **kwds)
        self._model["parameter_enable"] = 1
        self._model["saved_attribute_attributes"] = dict(
            valueof=dict(
                parameter_initial=[initial or 1],
                parameter_initial_enable=1,
                parameter_longname=longname,
                parameter_mmax=maximum,
                parameter_mmin=minimum,
                parameter_shortname=shortname or "",
                parameter_type=1,
            )
        )
        self._param = self._model["saved_attribute_attributes"]["valueof"]
        self._model["maximum"] = maximum
        self._model["minimum"] = minimum
        self._model["hint"] = hint or longname

    @property
    def longname(self):
        return self._param["parameter_longname"]

    @longname.setter
    def longname(self, value: str):
        self._param["parameter_longname"] = value

    @property
    def shortname(self):
        return self._param["parameter_shortname"]

    @shortname.setter
    def shortname(self, value: str):
        self._param["parameter_shortname"] = value

    @property
    def enable(self):
        return self._model["parameter_enable"]

    @enable.setter
    def enable(self, value: bool):
        self._model["parameter_enable"] = value

    @property
    def initial(self):
        return self._param["parameter_initial"]

    @initial.setter
    def initial(self, value: int):
        self._param["parameter_initial"] = value

    @property
    def initial_enable(self):
        return self._param["parameter_initial_enable"]

    @initial_enable.setter
    def initial_enable(self, value: bool):
        self._param["parameter_initial_enable"] = value

    @property
    def maximum(self):
        return self._model["maximum"]

    @maximum.setter
    def maximum(self, value: int):
        self._model["maximum"] = value
        self._param["parameter_mmax"] = value

    @property
    def minimum(self):
        return self._model["minimum"]

    @minimum.setter
    def minimum(self, value: int):
        self._model["minimum"] = value
        self._param["parameter_mmin"] = value

    @property
    def type(self):
        return self._param["parameter_type"]

    @type.setter
    def type(self, value: int):
        # FIXME: better to have an enum here
        assert 2 >= value >= 1
        self._param["parameter_type"] = value

    @property
    def hint(self):
        return self._model["hint"]

    @hint.setter
    def hint(self, value: str):
        self._model["hint"] = value


class FloatBox(Box):
    def __init__(
        self,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds,
    ):
        super().__init__("flonum", 1, 2, ["", "bang"], patching_rect, id, **kwds)


class FloatParam(FloatBox):
    def __init__(
        self,
        longname: str,
        initial: Optional[float] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        shortname: Optional[str] = None,
        id: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        hint: Optional[str] = None,
        **kwds,
    ):
        """int parameter object."""
        super().__init__(patching_rect, id, **kwds)
        self._model["parameter_enable"] = 1
        self._model["saved_attribute_attributes"] = dict(
            valueof=dict(
                parameter_initial=[initial or 1],
                parameter_initial_enable=1,
                parameter_longname=longname,
                parameter_mmax=maximum,
                parameter_mmin=minimum,
                parameter_shortname=shortname or "",
                parameter_type=1,
            )
        )
        self._param = self._model["saved_attribute_attributes"]["valueof"]
        self._model["maximum"] = maximum
        self._model["minimum"] = minimum
        self._model["hint"] = hint or longname

    @property
    def longname(self):
        return self._param["parameter_longname"]

    @longname.setter
    def longname(self, value: str):
        self._param["parameter_longname"] = value

    @property
    def shortname(self):
        return self._param["parameter_shortname"]

    @shortname.setter
    def shortname(self, value: str):
        self._param["parameter_shortname"] = value

    @property
    def enable(self):
        return self._model["parameter_enable"]

    @enable.setter
    def enable(self, value: bool):
        self._model["parameter_enable"] = value

    @property
    def initial(self):
        return self._param["parameter_initial"]

    @initial.setter
    def initial(self, value: int):
        self._param["parameter_initial"] = value

    @property
    def initial_enable(self):
        return self._param["parameter_initial_enable"]

    @initial_enable.setter
    def initial_enable(self, value: bool):
        self._param["parameter_initial_enable"] = value

    @property
    def maximum(self) -> float:
        return self._model["maximum"]

    @maximum.setter
    def maximum(self, value: float):
        self._model["maximum"] = value
        self._param["parameter_mmax"] = value

    @property
    def minimum(self) -> float:
        return self._model["minimum"]

    @minimum.setter
    def minimum(self, value: float):
        self._model["minimum"] = value
        self._param["parameter_mmin"] = value

    @property
    def type(self):
        return self._param["parameter_type"]

    @type.setter
    def type(self, value: int):
        # FIXME: better to have an enum here
        assert 2 >= value >= 1
        self._param["parameter_type"] = value

    @property
    def hint(self):
        return self._model["hint"]

    @hint.setter
    def hint(self, value: str):
        self._model["hint"] = value


class Patchline:
    def __init__(
        self,
        source: tuple[str, int],
        destination: tuple[str, int],
        order: int = 0,
        **kwds,
    ):
        src_id, src_outlet = tuple(source)
        dst_id, dst_inlet = tuple(destination)
        self._model = {
            "source": (src_id, src_outlet),
            "destination": (dst_id, dst_inlet),
            "order": order,
        }
        self._kwds = kwds

    def __repr__(self):
        return f"Patchline({self.source} -> {self.destination})"

    @classmethod
    def from_dict(cls, obj_dict: dict):
        """convert to `Patchline` object from dict"""
        patchline = cls(**obj_dict["patchline"])
        return patchline

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = self._model.copy()
        d.update(self._kwds)
        return dict(patchline=d)

    @property
    def src(self):
        """first object from source list"""
        return self.source[0]

    @property
    def dst(self):
        """first object from destination list"""
        return self.destination[0]

    @property
    def source(self) -> tuple[str, int]:
        return self._model["source"]

    @source.setter
    def source(self, value: tuple[str, int]):
        self._model["source"] = value

    @property
    def destination(self) -> tuple[str, int]:
        return self._model["destination"]

    @destination.setter
    def destination(self, value: tuple[str, int]):
        self._model["destination"] = value

    @property
    def order(self):
        return self._model["order"]

    @order.setter
    def order(self, value: int):
        self._model["order"] = value


class Patcher:
    """Core Patcher class describing a Max patchers from the ground up.

    Any Patcher can be converted to a .maxpat file.
    """

    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        title: Optional[str] = None,
        parent: Optional[Box] = None,
        classnamespace: Optional[str] = None,
        reset_on_render: bool = True,
        layout: str = "horizontal",
        auto_hints: bool = False,
        openinpresentation: int = 0,
    ):
        self._path = path
        self._parent = parent
        self._id_counter = 0
        self._link_counter = 0
        self._last_link: Optional[tuple[str, str]] = None
        self._node_ids: list[str] = []  # ids by order of creation
        self._objects: dict[str, Box] = {}  # dict of objects by id
        self._edge_ids: list[
            tuple[str, str]
        ] = []  # store edge-ids by order of creation
        self._reset_on_render = reset_on_render
        self._layout_mgr: LayoutManager = self.set_layout_mgr(layout)
        self._auto_hints = auto_hints
        self._model = {
            "fileversion": 1,
            "appversion": {
                "major": 8,
                "minor": 5,
                "revision": 5,
                "architecture": "x64",
                "modernui": 1,
            },
            "classnamespace": classnamespace or "box",
            "rect": Rect(85.0, 104.0, 640.0, 480.0),
            "bglocked": 0,
            "openinpresentation": openinpresentation,
            "default_fontsize": 12.0,
            "default_fontface": 0,
            "default_fontname": "Arial",
            "gridonopen": 1,
            "gridsize": [15.0, 15.0],
            "gridsnaponopen": 1,
            "objectsnaponopen": 1,
            "statusbarvisible": 2,
            "toolbarvisible": 1,
            "lefttoolbarpinned": 0,
            "toptoolbarpinned": 0,
            "righttoolbarpinned": 0,
            "bottomtoolbarpinned": 0,
            "toolbars_unpinned_last_save": 0,
            "tallnewobj": 0,
            "boxanimatetime": 200,
            "enablehscroll": 1,
            "enablevscroll": 1,
            "devicewidth": 0.0,
            "description": "",
            "digest": "",
            "tags": "",
            "style": "",
            "subpatcher_template": "",
            "assistshowspatchername": 0,
            "dependency_cache": [],
            "autosave": 0,
        }
        self.boxes = []
        self.lines = []
        self.title = title

    def __repr__(self):
        return f"{self.__class__.__name__}(path='{self._path}')"

    def __iter__(self):
        yield self
        for box in self.boxes:
            yield from iter(box)

    def get_id(self) -> str:
        """helper func to increment object ids"""
        self._id_counter += 1
        return f"obj-{self._id_counter}"

    @property
    def width(self) -> float:
        """width of patcher window."""
        return self.rect.w

    @property
    def height(self) -> float:
        """height of patcher windows."""
        return self.rect.h

    def set_layout_mgr(self, name: str) -> LayoutManager:
        """takes a name and returns an instance of a layout manager"""
        return {
            "horizontal": HorizontalLayoutManager,
            "vertical": VerticalLayoutManager,
        }[name](self)

    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """get box rect (position) via maxclass or layout_manager"""
        if maxclass:
            return self._layout_mgr.get_pos(maxclass)
        return self._layout_mgr.get_pos()

    @classmethod
    def from_dict(cls, patcher_dict: dict, save_to: Optional[str] = None) -> "Patcher":
        """create a patcher instance from a dict"""

        if save_to:
            patcher = cls(save_to)
        else:
            patcher = cls()
        patcher._model.update(patcher_dict)

        for box_dict in patcher._model["boxes"]:
            if "text" in box_dict["box"]:
                box = TextBox.from_dict(box_dict["box"])
            else:
                box = Box.from_dict(box_dict["box"])
            patcher.boxes.append(box)

        for line_dict in patcher._model["lines"]:
            line = Patchline.from_dict(line_dict)
            patcher.lines.append(line)

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
        d = self._model.copy()
        if not self._parent:
            return dict(patcher=d)
        return d

    def to_json(self) -> str:
        """cascade convert to json"""
        self.render()
        return json.dumps(self.to_dict(), indent=4)

    def render(self, reset: bool = False):
        """cascade convert py2max objects to dicts."""
        if reset or self._reset_on_render:
            self._model["boxes"] = []
            self._model["lines"] = []
        for box in self.boxes:
            box.render()
            self._model["boxes"].append(box.to_dict())
        self._model["lines"] = [line.to_dict() for line in self.lines]

    def save_as(self, path: Union[str, Path]):
        """save as .maxpat json file"""
        path = Path(path)
        if path.parent:
            path.parent.mkdir(exist_ok=True)
        self.render()
        with open(path, "w", encoding="utf8") as f:
            json.dump(self.to_dict(), f, indent=4)

    def save(self):
        """save as json .maxpat file"""
        if self._path:
            self.save_as(self._path)

    def add_patchline_by_index(
        self, src_id: str, dst_id: str, dst_inlet: int = 0, src_outlet: int = 0
    ) -> Patchline:
        """Patchline creation between two objects using stored indexes"""

        src = self._objects[src_id]
        dst = self._objects[dst_id]
        assert src.id and dst.id, f"object {src} and {dst} require ids"
        return self.add_patchline(src.id, src_outlet, dst.id, dst_inlet)

    def add_patchline(
        self, src_id: str, src_outlet: int, dst_id: str, dst_inlet: int
    ) -> Patchline:
        """primary patchline creation method"""

        # get order of lines between same pair of objects
        if (src_id, dst_id) == self._last_link:
            self._link_counter += 1
        else:
            self._link_counter = 0
            self._last_link = (src_id, dst_id)

        order = self._link_counter
        src, dst = [src_id, src_outlet], [dst_id, dst_inlet]
        patchline = Patchline(source=src, destination=dst, order=order)
        self.lines.append(patchline)
        self._edge_ids.append((src_id, dst_id))
        return patchline

    def add_line(
        self, src_obj: Box, dst_obj: Box, inlet: int = 0, outlet: int = 0
    ) -> Patchline:
        """convenience line adding taking objects with default outlet to inlet"""
        assert src_obj.id and dst_obj.id, f"objects {src_obj} and {dst_obj} require ids"
        return self.add_patchline(src_obj.id, outlet, dst_obj.id, inlet)

    def add_comment(
        self,
        text: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        justify: Optional[str] = None,
        **kwds,
    ) -> TextBox:
        """Add a basic comment object."""
        if justify:
            kwds["textjustification"] = {"left": 0, "center": 1, "right": 2}[justify]
        return self.add_box(
            TextBox(
                id=id or self.get_id(),
                text=text,
                maxclass="comment",
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            )
        )

    def add_associated_comment(
        self, box: "Box", comment: str, comment_pos: Optional[str] = None
    ):
        """add a comment associated with the object"""

        rect = box.patching_rect
        x, y, w, h = rect
        if h != self._layout_mgr.box_height:
            if box.maxclass in MAXCLASS_DEFAULTS:
                dh: float = 0.0
                _, _, _, dh = MAXCLASS_DEFAULTS[box.maxclass]["patching_rect"]
                rect = Rect(x, y, w, dh)
            else:
                h = self._layout_mgr.box_height
                rect = Rect(x, y, w, h)
        # rect = x, y, self._layout_mgr.box_width, self._layout_mgr.box_height
        if comment_pos:
            assert comment_pos in [
                "above",
                "below",
                "right",
                "left",
            ], f"comment:{comment} / comment_pos: {comment_pos}"
            patching_rect = getattr(self._layout_mgr, comment_pos)(rect)
        else:
            patching_rect = self._layout_mgr.above(rect)
        if comment_pos == "left":  # special case
            self.add_comment(comment, patching_rect, justify="right")
        else:
            self.add_comment(comment, patching_rect)

    def add_box(
        self,
        box: Box,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
    ) -> "Box":
        """registers the box and adds it to the patcher"""

        assert box.id, f"object {box} must have an id"
        self._node_ids.append(box.id)
        self._objects[box.id] = box
        self.boxes.append(box)
        if comment:
            self.add_associated_comment(box, comment, comment_pos)
        return box

    def add_textbox(
        self,
        text: str,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[list[str]] = None,
        patching_rect: Optional[Rect] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        id: Optional[str] = None,
        **kwds,
    ) -> TextBox:
        """Add a generic textbox object to the patcher.

        Looks up default attributes from a dictionary.
        """

        _maxclass, *tail = text.split()
        if _maxclass in MAXCLASS_DEFAULTS and not maxclass:
            maxclass = _maxclass

        kwds = self._textbox_helper(_maxclass, kwds)

        return self.add_box(
            TextBox(
                id=id or self.get_id(),
                text=text,
                maxclass=maxclass or "newobj",
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 0,
                patching_rect=patching_rect
                    or (self.get_pos(maxclass) if maxclass else self.get_pos()),
                outlettype=outlettype or [""],
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
    ) -> TextBox:
        """create a param-linke attrui entry"""
        if autovar:
            kwds["varname"] = name

        return self.add_box(
            TextBox(
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
    ) -> TextBox:
        """Add a subpatcher object."""

        return self.add_box(
            TextBox(
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

    def add_gen(self, tilde=False, **kwds):
        """Add a gen object."""
        text = "gen~" if tilde else "gen"
        return self.add_subpatcher(
            text, patcher=Patcher(parent=self, classnamespace="dsp.gen"), **kwds
        )

    def add_gen_tilde(self, **kwds):
        """Add a gen~ object."""
        return self.add_gen(tilde=True, **kwds)

    def add_rnbo(self, text: str = "rnbo~", **kwds):
        """Add an rnbo~ object."""
        if "inletInfo" not in kwds:
            if "numinlets" in kwds:
                inletInfo: dict[str, list] = {"IOInfo": []}
                for i in range(kwds["numinlets"]):
                    inletInfo["IOInfo"].append(
                        dict(comment="", index=i + 1, tag=f"in{i+1}", type="signal")
                    )
                kwds["inletInfo"] = inletInfo
        if "outletInfo" not in kwds:
            if "numoutlets" in kwds:
                outletInfo: dict[str, list] = {"IOInfo": []}
                for i in range(kwds["numoutlets"]):
                    outletInfo["IOInfo"].append(
                        dict(comment="", index=i + 1, tag=f"out{i+1}", type="signal")
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

    @property
    def title(self) -> Optional[str]:
        if "title" in self._model:
            return self._model["title"]
        return None

    @title.setter
    def title(self, value: Optional[str]):
        if value:
            self._model["title"] = value

    @property
    def fileversion(self):
        return self._model["fileversion"]

    @fileversion.setter
    def fileversion(self, value: int):
        self._model["fileversion"] = value

    @property
    def appversion(self):
        return self._model["appversion"]

    @appversion.setter
    def appversion(self, value: dict):
        self._model["appversion"] = value

    @property
    def classnamespace(self):
        return self._model["classnamespace"]

    @classnamespace.setter
    def classnamespace(self, value: str):
        self._model["classnamespace"] = value

    @property
    def rect(self):
        return self._model["rect"]

    @rect.setter
    def rect(self, value: Rect):
        self._model["rect"] = value

    @property
    def bglocked(self):
        return self._model["bglocked"]

    @bglocked.setter
    def bglocked(self, value: int):
        self._model["bglocked"] = value

    @property
    def openinpresentation(self):
        return self._model["openinpresentation"]

    @openinpresentation.setter
    def openinpresentation(self, value: int):
        self._model["openinpresentation"] = value

    @property
    def default_fontsize(self):
        return self._model["default_fontsize"]

    @default_fontsize.setter
    def default_fontsize(self, value: float):
        self._model["default_fontsize"] = value

    @property
    def default_fontface(self):
        return self._model["default_fontface"]

    @default_fontface.setter
    def default_fontface(self, value: int):
        self._model["default_fontface"] = value

    @property
    def default_fontname(self):
        return self._model["default_fontname"]

    @default_fontname.setter
    def default_fontname(self, value: str):
        self._model["default_fontname"] = value

    @property
    def gridonopen(self):
        return self._model["gridonopen"]

    @gridonopen.setter
    def gridonopen(self, value: int):
        self._model["gridonopen"] = value

    @property
    def gridsize(self):
        return self._model["gridsize"]

    @gridsize.setter
    def gridsize(self, value: list):
        self._model["gridsize"] = value

    @property
    def gridsnaponopen(self):
        return self._model["gridsnaponopen"]

    @gridsnaponopen.setter
    def gridsnaponopen(self, value: int):
        self._model["gridsnaponopen"] = value

    @property
    def objectsnaponopen(self):
        return self._model["objectsnaponopen"]

    @objectsnaponopen.setter
    def objectsnaponopen(self, value: int):
        self._model["objectsnaponopen"] = value

    @property
    def statusbarvisible(self):
        return self._model["statusbarvisible"]

    @statusbarvisible.setter
    def statusbarvisible(self, value: int):
        self._model["statusbarvisible"] = value

    @property
    def toolbarvisible(self):
        return self._model["toolbarvisible"]

    @toolbarvisible.setter
    def toolbarvisible(self, value: int):
        self._model["toolbarvisible"] = value

    @property
    def lefttoolbarpinned(self):
        return self._model["lefttoolbarpinned"]

    @lefttoolbarpinned.setter
    def lefttoolbarpinned(self, value: int):
        self._model["lefttoolbarpinned"] = value

    @property
    def toptoolbarpinned(self):
        return self._model["toptoolbarpinned"]

    @toptoolbarpinned.setter
    def toptoolbarpinned(self, value: int):
        self._model["toptoolbarpinned"] = value

    @property
    def righttoolbarpinned(self):
        return self._model["righttoolbarpinned"]

    @righttoolbarpinned.setter
    def righttoolbarpinned(self, value: int):
        self._model["righttoolbarpinned"] = value

    @property
    def bottomtoolbarpinned(self):
        return self._model["bottomtoolbarpinned"]

    @bottomtoolbarpinned.setter
    def bottomtoolbarpinned(self, value: int):
        self._model["bottomtoolbarpinned"] = value

    @property
    def toolbars_unpinned_last_save(self):
        return self._model["toolbars_unpinned_last_save"]

    @toolbars_unpinned_last_save.setter
    def toolbars_unpinned_last_save(self, value: int):
        self._model["toolbars_unpinned_last_save"] = value

    @property
    def tallnewobj(self):
        return self._model["tallnewobj"]

    @tallnewobj.setter
    def tallnewobj(self, value: int):
        self._model["tallnewobj"] = value

    @property
    def boxanimatetime(self):
        return self._model["boxanimatetime"]

    @boxanimatetime.setter
    def boxanimatetime(self, value: int):
        self._model["boxanimatetime"] = value

    @property
    def enablehscroll(self):
        return self._model["enablehscroll"]

    @enablehscroll.setter
    def enablehscroll(self, value: int):
        self._model["enablehscroll"] = value

    @property
    def enablevscroll(self):
        return self._model["enablevscroll"]

    @enablevscroll.setter
    def enablevscroll(self, value: int):
        self._model["enablevscroll"] = value

    @property
    def devicewidth(self):
        return self._model["devicewidth"]

    @devicewidth.setter
    def devicewidth(self, value: float):
        self._model["devicewidth"] = value

    @property
    def description(self):
        return self._model["description"]

    @description.setter
    def description(self, value: str):
        self._model["description"] = value

    @property
    def digest(self):
        return self._model["digest"]

    @digest.setter
    def digest(self, value: str):
        self._model["digest"] = value

    @property
    def tags(self):
        return self._model["tags"]

    @tags.setter
    def tags(self, value: str):
        self._model["tags"] = value

    @property
    def style(self):
        return self._model["style"]

    @style.setter
    def style(self, value: str):
        self._model["style"] = value

    @property
    def subpatcher_template(self):
        return self._model["subpatcher_template"]

    @subpatcher_template.setter
    def subpatcher_template(self, value: str):
        self._model["subpatcher_template"] = value

    @property
    def assistshowspatchername(self):
        return self._model["assistshowspatchername"]

    @assistshowspatchername.setter
    def assistshowspatchername(self, value: int):
        self._model["assistshowspatchername"] = value

    @property
    def dependency_cache(self):
        return self._model["dependency_cache"]

    @dependency_cache.setter
    def dependency_cache(self, value: list):
        self._model["dependency_cache"] = value

    @property
    def autosave(self):
        return self._model["autosave"]

    @autosave.setter
    def autosave(self, value: int):
        self._model["autosave"] = value


if __name__ == "__main__":
    # p = Patcher.from_file("../data/nested.maxpat", save_to="out.maxpat")
    # p.save()

    p = Patcher("out.maxpat")
    osc = p.add_textbox("cycle~ 440")
    dac = p.add_textbox("ezdac~")
    p.add_line(osc, dac)
    p.add_line(osc, dac, inlet=1)
    p.save()
