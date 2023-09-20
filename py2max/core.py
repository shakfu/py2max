import abc
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, NamedTuple, Optional, Tuple, Union

from pydantic import (BaseModel, Field, ConfigDict, ValidationError,
                      model_serializer, model_validator, validator)

from .common import Rect
from .maxclassdb import MAXCLASS_DEFAULTS

# ---------------------------------------------------------------------------
# CONSTANTS

MAX_VER_MAJOR = 8
MAX_VER_MINOR = 5
MAX_VER_REVISION = 5

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


class Rect(NamedTuple):
    x: float
    y: float
    w: float
    h: float


class Box(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=True)

    id: str
    text: Optional[str] = None
    maxclass: str = "newobj"
    numinlets: int = 0
    numoutlets: int = 1
    outlettype: list[str] = [""]
    patching_rect: Rect = Rect(x=0, y=0, w=62, h=22)
    patcher: Optional["Patcher"] = None

    def __iter__(self):
        yield self
        if self.patcher:
            yield from iter(self.patcher)

    @validator('text')
    def text_is_some(cls, v: str):
        if v is None:
            raise ValidationError('Cannot set text to None')
        return str(v)

    @model_serializer
    def serialize_box(self):
        box = {}
        for f in self.model_fields:
            val = getattr(self, f)
            if val is not None:
                box[f] = val
        box.update(self.__pydantic_extra__)
        return dict(box=box)

    @model_validator(mode="before")
    def validate_box(cls, data: dict) -> dict:
        result = defaultdict(dict, data)
        if "box" in result:
           return dict(result["box"])
        else:
            return dict(data)



class Patchline(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=True)

    source: tuple[str, int]
    destination: tuple[str, int]
    order: int = 0

    @model_serializer
    def serialize_patchline(self):
        line = {}
        for f in self.model_fields:
            line[f] = getattr(self, f)
        line.update(self.__pydantic_extra__)
        return dict(patchline=line)

    @model_validator(mode="before")
    def validate_patchline(cls, data: dict) -> dict:
        result = defaultdict(dict, data)
        if "patchline" in result:
           return dict(result["patchline"])
        else:
            return dict(data)

class Patcher(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=True)

    # internal (not exported)
    path: Optional[str | Path] = Field(default=None, exclude=True)

    # private (not exported)
    _id_counter: int = 0
    _link_counter: int = 0

    # api
    title: str = ""
    fileversion: int = 1
    appversion: dict = {
        "major": MAX_VER_MAJOR,
        "minor": MAX_VER_MINOR,
        "revision": MAX_VER_REVISION,
        "architecture": "x64",
        "modernui": 1,
    }
    classnamespace: str = "box"
    rect: Rect = Rect(85.0, 104.0, 640.0, 480.0)
    bglocked: int = 0
    openinpresentation: int = 0
    default_fontsize: float = 12.0
    default_fontface: int = 0
    default_fontname: str = "Arial"
    gridonopen: int = 1
    gridsize: tuple[float, float] = (15.0, 15.0)
    gridsnaponopen: int = 1
    objectsnaponopen: int = 1
    statusbarvisible: int = 2
    toolbarvisible: int = 1
    lefttoolbarpinned: int = 0
    toptoolbarpinned: int = 0
    righttoolbarpinned: int = 0
    bottomtoolbarpinned: int = 0
    toolbars_unpinned_last_save: int = 0
    tallnewobj: int = 0
    boxanimatetime: int = 200
    enablehscroll: int = 1
    enablevscroll: int = 1
    devicewidth: float = 0.0
    description: str = ""
    digest: str = ""
    tags: str = ""
    style: str = ""
    subpatcher_template: str = ""
    assistshowspatchername: int = 0
    dependency_cache: list = []
    autosave: int = 0
    boxes: list[Box] = []
    lines: list[Patchline] = []

    def __iter__(self):
        yield self
        for box in self.boxes:
            yield from iter(box)

    @classmethod
    def from_dict(cls, patcher_dict: dict, save_to: Optional[str | Path] = None) -> "Patcher":
        """create a patcher instance from a dict"""
        patcher = cls.model_validate(patcher_dict, strict=True)
        if save_to:
            patcher.path = save_to
        return patcher

    @classmethod
    def from_file(cls, path: str | Path, save_to: Optional[str | Path] = None) -> "Patcher":
        """create a patcher instance from a .maxpat json file"""
        with open(path, encoding="utf8") as f:
            patcher = cls.model_validate_json(f.read())
        if save_to:
            patcher.path = save_to
        return patcher

    @model_serializer
    def serialize_box(self):
        exclude = ['path']
        patcher = {}
        for f in self.model_fields:
            if f in exclude:
                continue
            val = getattr(self, f)
            if val is not None:
                patcher[f] = val
        patcher.update(self.__pydantic_extra__)
        return dict(patcher=patcher)

    @model_validator(mode="before")
    def validate_patcher(cls, data: dict) -> dict:
        result = defaultdict(dict, data)
        if "patcher" in result:
           return dict(result["patcher"])
        else:
            return dict(data)

    @property
    def width(self) -> float:
        """width of patcher window."""
        return self.rect.w

    @property
    def height(self) -> float:
        """height of patcher windows."""
        return self.rect.h

    def save_as(self, path: str | Path):
        """save as .maxpat json file"""
        path = Path(path)
        if path.parent:
            path.parent.mkdir(exist_ok=True)
        with open(path, "w", encoding="utf8") as f:
            f.write(self.model_dump_json(indent=4))

    def save(self):
        """save as json .maxpat file"""
        if self.path:
            self.save_as(self.path)

    def get_id(self) -> str:
        """helper func to increment object ids"""
        self._id_counter += 1
        return f"obj-{self._id_counter}"

    def set_layout_mgr(self, name: str) -> LayoutManager:
        """takes a name and returns an instance of a layout manager"""
        return {
            "horizontal": HorizontalLayoutManager,
            "vertical": VerticalLayoutManager,
        }[name](self)

    def add_textbox( 
        self,
        text: str,
        maxclass: str = "newobj",
        numinlets: int = 0,
        numoutlets: int = 1,
        outlettype: list[str] = [""],
        patching_rect: Rect = Rect(x=0, y=0, w=62, h=22),
        patcher: Optional["Patcher"] = None,
        id: Optional[str] = None,
        **kwds,
    ):
        box = Box(
            text=text,
            id=id or self.get_id(),
            maxclass=maxclass,
            numinlets=numinlets,
            numoutlets=numoutlets,
            outlettype=outlettype,
            patching_rect=patching_rect,
            patcher=patcher,
            **kwds,
        )
        self.boxes.append(box)
        return box
    
    # alias
    add = add_textbox

    def add_line(self, src: Box, dst: Box, outlet=0, inlet=0):
        self._link_counter += 1
        line = Patchline(
            source=(src.id, outlet),
            destination=(dst.id, inlet),
            order=self._link_counter,
        )
        self.lines.append(line)
    
    # alias
    link = add_line
