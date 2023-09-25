"""py2max.core

A library to generate .maxpat patcher files.

This variant uses pydantic (v2) as its validation and transformation
engine to drive the round-trip conversion between 
.maxpat (JSON) <-> python objects

basic usage:

    >>> p = Patcher('out.maxpat')
    >>> osc1 = p.add_box('cycle~ 440')
    >>> gain = p.add_box('gain~')
    >>> dac = p.add_box('ezdac~')
    >>> p.add_line(osc1, gain)
    >>> p.add_line(gain, dac)
    >>> p.save()

"""
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    ValidationError,
    model_serializer,
    model_validator,
    field_validator,
)

from .common import Rect
from .maxclassdb import MAXCLASS_DEFAULTS
from .layout import LayoutManager, HorizontalLayoutManager, VerticalLayoutManager

# ---------------------------------------------------------------------------
# CONSTANTS

MAX_VER_MAJOR = 8
MAX_VER_MINOR = 5
MAX_VER_REVISION = 5

# ---------------------------------------------------------------------------
# Primary Classes

class Box(BaseModel):
    """General Box class to specify Max 'box' objects

    subclass of pydantic.BaseModel
    """
    model_config = ConfigDict(extra="allow", validate_assignment=True)

    id: str
    text: Optional[str] = None
    maxclass: str = "newobj"
    numinlets: int = 0
    numoutlets: int = 1
    outlettype: list[str] = [""]
    patching_rect: Rect = Rect(x=0, y=0, w=62, h=22)
    patcher: Optional["Patcher"] = None

    # def __repr__(self):
    #     return f"Box(id='{self.id}', maxclass='{self.maxclass}')"

    def __iter__(self):
        yield self
        if self.patcher:
            yield from iter(self.patcher)

    @field_validator("text")
    def text_is_valid(cls, value: str):
        """Exclude 'text' field in export if it is None"""
        if value is None:
            raise ValidationError("Cannot set text to None")
        return str(value)

    @model_serializer
    def serialize_box(self):
        """Custom serialization of Box object"""
        box = {}
        for f in self.model_fields:
            val = getattr(self, f)
            if val is not None:
                box[f] = val
        box.update(self.__pydantic_extra__)
        return dict(box=box)

    @model_validator(mode="before")
    def validate_box(cls, data: dict) -> dict:
        """Customize export from 'dict_result -> dict(box=dict_result)'"""
        result = defaultdict(dict, data)
        if "box" in result:
            return dict(result["box"])
        else:
            return dict(data)

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


class Patchline(BaseModel):
    """General Patchline class to specify Max 'patchline' objects

    subclass of pydantic.BaseModel
    """
    model_config = ConfigDict(extra="allow", validate_assignment=True)

    source: tuple[str, int]
    destination: tuple[str, int]
    order: int = 0

    # def __repr__(self):
    #     return f"Patchline(source={self.source}, destination={self.destination})"

    @property
    def src(self):
        return self.source[0]

    @property
    def dst(self):
        return self.destination[0]

    @model_serializer
    def serialize_patchline(self):
        """Custom serialization of Patchline object"""
        line = {}
        for f in self.model_fields:
            line[f] = getattr(self, f)
        line.update(self.__pydantic_extra__)
        return dict(patchline=line)

    @model_validator(mode="before")
    def validate_patchline(cls, data: dict) -> dict:
        """Customize export from 'dict_result -> dict(patchline=dict_result)'"""
        result = defaultdict(dict, data)
        if "patchline" in result:
            return dict(result["patchline"])
        else:
            return dict(data)


class Patcher(BaseModel):
    """General Patcher class to specify Max patcher objects

    subclass of pydantic.BaseModel
    """
    model_config = ConfigDict(extra="allow", validate_assignment=True)

    # private parameters / attributes (not exported)
    path: Optional[str | Path] = Field(default=None, exclude=True)
    layout: str = Field(default="horizontal", exclude=True)
    parent: Optional[Box] = Field(default=None, exclude=True)
    is_subpatcher: bool = Field(default=False, exclude=True)

    # private non-param attributes (not exported)
    _auto_hints: bool = False
    _layout: str = "horizontal"
    _layout_mgr: LayoutManager 
    _id_counter: int = 0
    _link_counter: int = 0
    _last_link: Optional[tuple[str, str]] = None
    _node_ids: list[str] = []  # ids by order of creation
    _objects: dict[str, Box] = {}  # dict of objects by id
    _edge_ids: list[tuple[str, str]] = []  # store edge-ids by order of creation

    # public api
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

    # def __repr__(self):
    #     return f"Patcher(path='{self.path}, boxes={self.boxes}, lines={self.lines}')"

    def __iter__(self):
        yield self
        for box in self.boxes:
            yield from iter(box)

    def model_post_init(self, __context: Any):
        """run after instance intialization"""
        self.set_layout_mgr(self.layout)

    @classmethod
    def from_dict(
        cls, patcher_dict: dict, save_to: Optional[str | Path] = None
    ) -> "Patcher":
        """create a patcher instance from a dict"""
        patcher = cls.model_validate(patcher_dict, strict=True)
        if save_to:
            patcher.path = save_to
        return patcher

    @classmethod
    def from_file(
        cls, path: str | Path, save_to: Optional[str | Path] = None
    ) -> "Patcher":
        """create a patcher instance from a .maxpat json file"""
        with open(path, encoding="utf8") as f:
            patcher = cls.model_validate_json(f.read())
        if save_to:
            patcher.path = save_to
        return patcher

    @model_serializer
    def serialize_patcher(self):
        """Customize serialization of Patcher objects"""
        exclude = ["path"]
        patcher = {}
        for f in self.model_fields:
            if f in exclude:
                continue
            val = getattr(self, f)
            if val is not None:
                patcher[f] = val
        patcher.update(self.__pydantic_extra__)
        if self.is_subpatcher:
            return dict(patcher)
        else:
            return dict(patcher=patcher)

    @model_validator(mode="before")
    def validate_patcher(cls, data: dict) -> dict:
        """Customize export from 'dict_result -> dict(patcher=dict_result)'"""
        result = defaultdict(dict, data)
        if "patcher" in result:
            return dict(result["patcher"])
        else:
            return dict(data)

    @property
    def _maxclass_methods(self) -> dict:
        """returns a dict mapping shortnames to custom add_* methods"""
        return {
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

    def set_layout_mgr(self, name: str):
        """sets the patcher layout manager"""
        mgrs = {
            "horizontal": HorizontalLayoutManager,
            "vertical": VerticalLayoutManager,
        }
        assert name in mgrs, f"must be one of {mgrs.keys()}"
        self.layout = name
        self._layout_mgr = mgrs[self.layout](self)

    def get_pos(self, maxclass: Optional[str] = None) -> Rect:
        """get box rect (position) via maxclass or layout_manager"""
        if maxclass:
            return self._layout_mgr.get_pos(maxclass)
        return self._layout_mgr.get_pos()

    # def find(self, text: str) -> list[Box]:
    #     """finds (recursively) box objects by maxclass or text

    #     returns list of matching boxes if found else an empty list
    #     """
    #     results = []
    #     for obj in self:
    #         if isinstance(obj, Box):
    #             if text in obj.maxclass:
    #                 results.append(obj)
    #             if hasattr(obj, "text"):
    #                 if text in obj.text:
    #                     results.append(obj)
    #     return results

    def find(self, text: str) -> Optional[Box]:
        """find (recursively) box object by maxclass or type

        returns box if found else None
        """
        for obj in self:
            if isinstance(obj, Box):
                if text in obj.maxclass:
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
                return box
            if hasattr(box, "text"):
                if box.text and box.text.startswith(text):
                    return box
        return None

    def find_box_with_index(self, text: str) -> Optional[Tuple[int, "Box"]]:
        """find box object by maxclass or type

        returns (index, box) if found
        """
        for i, box in enumerate(self.boxes):
            if box.maxclass == text:
                return (i, box)
            if hasattr(box, "text"):
                if box.text and box.text.startswith(text):
                    return (i, box)
        return None

    def _add_box(
        self,
        box: Box,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
    ) -> Box:
        """registers the box and adds it to the patcher"""

        assert box.id, f"object {box} must have an id"
        self._node_ids.append(box.id)
        self._objects[box.id] = box
        self.boxes.append(box)
        if comment:
            self.add_associated_comment(box, comment, comment_pos)
        return box

    def add_comment(
        self,
        text: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        justify: Optional[str] = None,
        **kwds,
    ) -> Box:
        """Add a basic comment object."""
        if justify:
            kwds["textjustification"] = {"left": 0, "center": 1, "right": 2}[justify]
        return self._add_box(
            Box(
                id=id or self.get_id(),
                text=text,
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            )
        )

    def add_associated_comment(
        self, box: Box, comment: str, comment_pos: Optional[str] = None
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
    ) -> Box:
        """Add a generic textbox object to the patcher.

        Looks up default attributes from a dictionary.
        """
        _maxclass, *tail = text.split()
        if _maxclass in MAXCLASS_DEFAULTS and not maxclass:
            maxclass = _maxclass

        kwds = self._box_helper(_maxclass, kwds)

        return self._add_box(
            Box(
                id=id or self.get_id(),
                text=text,
                maxclass=maxclass or "newobj",
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 0,
                outlettype=outlettype or [""],
                patching_rect=patching_rect
                or (self.get_pos(maxclass) if maxclass else self.get_pos()),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    # alias
    # add = add_box

    def _box_helper(self, maxclass, kwds: dict) -> dict:
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
        src, dst = (src_id, src_outlet), (dst_id, dst_inlet)
        patchline = Patchline(source=src, destination=dst, order=order)
        self.lines.append(patchline)
        self._edge_ids.append((src_id, dst_id))
        return patchline

    def add_line(
        self, src: Box, dst: "Box", inlet: int = 0, outlet: int = 0
    ) -> Patchline:
        """convenience line adding taking objects with default outlet to inlet"""
        assert src.id and dst.id, f"objects {src} and {dst} require ids"
        return self.add_patchline(src.id, outlet, dst.id, inlet)

    # def add_line(self, src: Box, dst: Box, outlet=0, inlet=0):
    #     self._link_counter += 1
    #     line = Patchline(
    #         source=(src.id, outlet),
    #         destination=(dst.id, inlet),
    #         order=self._link_counter,
    #     )
    #     self.lines.append(line)

    # alias
    link = add_line

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
        return self.add_box(text=value, **kwds)

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
    ) -> Box:
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

        return self._add_box(
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
    ) -> Box:
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
    ) -> Box:
        """Add a max message."""

        return self._add_box(
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

    def add_intbox(
        self,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds,
    ) -> Box:
        """Add an int box object."""

        return self._add_box(
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
    ) -> Box:
        """Add an float box object."""

        return self._add_box(
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
    ) -> Box:
        """Add a float parameter object."""

        return self._add_box(
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
    ) -> Box:
        """Add an int parameter object."""

        return self._add_box(
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
    ) -> Box:
        """create a param-linke attrui entry"""
        if autovar:
            kwds["varname"] = name

        return self._add_box(
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
    ) -> Box:
        """Add a subpatcher object."""

        if patcher:
            patcher.is_subpatcher = True
        else:
            patcher = Patcher(is_subpatcher=True)
        box = Box(
            id=id or self.get_id(),
            text=text,
            maxclass=maxclass or "newobj",
            numinlets=numinlets or 1,
            numoutlets=numoutlets or 0,
            outlettype=outlettype or [""],
            patching_rect=patching_rect or self.get_pos(),
            patcher=patcher,
            **kwds,
        )
        return self._add_box(box)

    def add_gen(self, tilde=False, **kwds):
        """Add a gen object."""
        text = "gen~" if tilde else "gen"
        return self.add_subpatcher(text, 
            patcher=Patcher(add_subpatcher = True, classnamespace="dsp.gen"), **kwds)

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
            text, patcher=Patcher(classnamespace="rnbo"), **kwds
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
        return self._add_box(
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
        return self._add_box(
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
        return self._add_box(
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
        return self._add_box(
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

        return self._add_box(
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

        return self._add_box(
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
