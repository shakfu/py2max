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
import json
import os
from typing import Type
from collections import namedtuple

from .maxclassdb import MAXCLASS_DEFAULTS


# ---------------------------------------------------------------------------
# CONSTANTS

MAX_VER_MAJOR = 8
MAX_VER_MINOR = 5
MAX_VER_REVISION = 5

# ---------------------------------------------------------------------------
# Utility Classes and functions

Rect = namedtuple("Rect", "x y w h")


# ---------------------------------------------------------------------------
# Primary Classes


class LayoutManager:
    """Utility class to help with object layout.
    
    This is a basic horizontal layout manager.
    i.e. objects flow and wrap to the right.
    """
    DEFAULT_PAD = 1.5*32.0
    DEFAULT_BOX_WIDTH = 66.0
    DEFAULT_BOX_HEIGHT = 22.0
    DEFAULT_COMMENT_PAD = 2

    def __init__(
        self,
        parent: "Patcher",
        pad: int = None,
        box_width: int = None,
        box_height: int = None,
        comment_pad: int = None,
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

    def get_rect_from_maxclass(self, maxclass):
        """retrieves default patching_rect from defaults dictionary."""
        try:
            rect = MAXCLASS_DEFAULTS[maxclass]["patching_rect"]
            return Rect(*rect)
        except KeyError:
            return

    def get_absolute_pos(self, rect: Rect):
        """returns an absolute position for the object"""
        x, y, w, h = tuple(rect)

        pad = self.pad

        if x > 0.5 * self.parent.width:
            x1 = x - (w + pad)
            x = x1 - (x1 - self.parent.width) if x1 > self.parent.width else x1
        else:
            x1 = x + pad

        print("x1", x1)

        y1 = y - (h + pad)
        y = y1 - (y1 - self.parent.height) if y1 > self.parent.height else y1

        return [x, y, w, h]

    def get_relative_pos(self, rect: Rect):
        """returns a relative horizontal position for the object"""
        x, y, w, h = tuple(rect)

        pad = self.pad  # 32.0

        x_shift = 3 * pad * self.x_layout_counter
        y_shift = 1.5 * pad * self.y_layout_counter
        x = pad + x_shift

        self.x_layout_counter += 1
        if x + w + 2 * pad > self.parent.width:
            self.x_layout_counter = 0
            self.y_layout_counter += 1

        y = pad + y_shift

        return [x, y, w, h]

    def get_relative_pos_v(self, rect: Rect):
        """returns a relative vertical position for the object"""
        x, y, w, h = tuple(rect)

        pad = self.pad  # 32.0

        x_shift = 3 * pad * self.x_layout_counter
        y_shift = 1.5 * pad * self.y_layout_counter
        y = pad + y_shift

        self.y_layout_counter += 1
        if y + h + 2 * pad > self.parent.height:
        # if y + h + 2 * pad > 300:
            self.x_layout_counter += 1
            self.y_layout_counter = 0

        x = pad + x_shift        

        return [x, y, w, h]

    def get_pos(self, maxclass: str = None):
        """helper func providing very rough auto-layout of objects"""
        x = 0
        y = 0
        w = self.box_width  # 66.0
        h = self.box_height  # 22.0

        if maxclass:
            mclass_rect = self.get_rect_from_maxclass(maxclass)
            if mclass_rect and (mclass_rect.x or mclass_rect.y):
                if mclass_rect.x:
                    x = int(mclass_rect.x * self.parent.width)
                if mclass_rect.y:
                    y = int(mclass_rect.y * self.parent.height)

                _rect = Rect(x, y, mclass_rect.w, mclass_rect.h)
                return self.get_absolute_pos(_rect)

        _rect = Rect(x, y, w, h)
        return self.get_relative_pos(_rect)

    @property
    def patcher_rect(self):
        """return rect coordinates of the parent patcher"""
        return self.parent.rect

    def above(self, rect):
        """Return a position of a comment above the object"""
        x, y, w, h = rect
        return [x, y - h, w, h]

    def below(self, rect):
        """Return a position of a comment below the object"""
        x, y, w, h = rect
        return [x, y + h, w, h]

    def left(self, rect):
        """Return a position of a comment left of the object"""
        x, y, w, h = rect
        return [x - (w + self.comment_pad), y, w, h]

    def right(self, rect):
        """Return a position of a comment right of the object"""
        x, y, w, h = rect
        return [x + (w + self.comment_pad), y, w, h]


class VerticalLayoutManager(LayoutManager):
    """Utility class to help with obadject layout.
    
    This is a basic horizontal layout manager.
    i.e. objects fill from top to bottom of the 
    grid and and wrap vertically.
    """

    def get_relative_pos(self, rect: Rect):
        """returns a relative vertical position for the object"""
        x, y, w, h = tuple(rect)

        pad = self.pad  # 32.0

        x_shift = 3 * pad * self.x_layout_counter
        y_shift = 1.5 * pad * self.y_layout_counter
        y = pad + y_shift

        self.y_layout_counter += 1
        if y + h + 2 * pad > self.parent.height:
        # if y + h + 2 * pad > 300:
            self.x_layout_counter += 1
            self.y_layout_counter = 0

        x = pad + x_shift        

        return [x, y, w, h]



class Patcher:
    """Core Patcher class describing a Max patchers from the ground up.

    Any Patcher can be converted to a .maxpat file.
    """

    def __init__(
        self,
        path: str = None,
        parent: "Patcher" = None,
        classnamespace: str = None,
        reset_on_render: bool = True,
        layout_mgr_class: Type[LayoutManager] = None,
        auto_hints: bool = False,
        openinpresentation: int = 0,
    ):
        self._path = path
        self._parent = parent
        self._node_ids = []  # ids by order of creation
        self._objects = {}  # dict of objects by id
        self._boxes = []  # store child objects (boxes, etc.)
        self._lines = []  # store patchline objects
        self._edge_ids = []  # store edge-ids by order of creation
        self._id_counter = 0
        self._link_counter = 0
        self._last_link = None
        self._reset_on_render = reset_on_render
        self._layout_mgr = (
            layout_mgr_class(self) if layout_mgr_class else LayoutManager(self)
        )
        self._auto_hints = auto_hints
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

        # begin max attributes
        self.fileversion = 1
        self.appversion = {
            "major": MAX_VER_MAJOR,
            "minor": MAX_VER_MINOR,
            "revision": MAX_VER_REVISION,
            "architecture": "x64",
            "modernui": 1,
        }
        self.classnamespace = classnamespace or "box"
        self.rect = [85.0, 104.0, 640.0, 480.0]
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
        self.boxes = []
        self.lines = []
        self.parameters = {}
        self.dependency_cache = []
        self.autosave = 0

    def __repr__(self):
        return f"{self.__class__.__name__}(path='{self._path}')"

    def __iter__(self):
        yield self
        for box in self._boxes:
            yield from iter(box)

    @property
    def width(self):
        """width of patcher window."""
        return self.rect[2]

    @property
    def height(self):
        """height of patcher windows."""
        return self.rect[3]

    @classmethod
    def from_dict(cls, patcher_dict):
        """create a patcher instance from a dict"""

        patcher = cls()
        patcher.__dict__.update(patcher_dict)

        for box_dict in patcher.boxes:
            box = box_dict["box"]
            b = Box.from_dict(box)
            # b = patcher.box_from_dict(box)
            patcher._boxes.append(b)

        for line_dict in patcher.lines:
            line = line_dict["patchline"]
            pl = Patchline.from_dict(line)
            patcher._lines.append(pl)

        return patcher

    @classmethod
    def from_file(cls, path, save_to: str = None):
        """create a patcher instance from a .maxpat json file"""

        with open(path) as f:
            maxpat = json.load(f)
        return Patcher.from_dict(maxpat["patcher"])

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = vars(self).copy()
        to_del = [k for k in d if k.startswith("_")]
        for k in to_del:
            del d[k]
        if not self._parent:
            return dict(patcher=d)
        else:
            return d

    def to_json(self):
        """cascade convert to json"""
        self.render()
        return json.dumps(self.to_dict(), indent=4)

    def render(self, reset=False):
        """cascade convert py2max objects to dicts."""
        if reset or self._reset_on_render:
            self.boxes = []
            self.lines = []
        for box in self._boxes:
            box.render()
            self.boxes.append(box.to_dict())
        self.lines = [line.to_dict() for line in self._lines]

    def saveas(self, path):
        """save as .maxpat json file"""
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        self.render()
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=4)

    def save(self):
        """save as json .maxpat file"""
        self.saveas(self._path)

    def get_id(self):
        """helper func to increment object ids"""
        self._id_counter += 1
        return f"obj-{self._id_counter}"

    def get_pos(self, maxclass=None):
        if maxclass:
            return self._layout_mgr.get_pos(maxclass)
        else:
            return self._layout_mgr.get_pos()

    def add_box(self, box, comment=None, comment_pos=None):
        """registers the box and adds it to the patcher"""

        self._node_ids.append(box.id)
        self._objects[box.id] = box
        self._boxes.append(box)
        if comment:
            self.add_associated_comment(box, comment, comment_pos)
        return box

    def add_associated_comment(self, box: "Box", comment: str, comment_pos: str = None):
        """add a comment associated with the object"""

        rect = box.patching_rect.copy()
        # normalize dimensions
        # rect = None
        x, y, w, h  = rect
        if h != self._layout_mgr.box_height:
            if box.maxclass in MAXCLASS_DEFAULTS:
                _, _, _, dh = MAXCLASS_DEFAULTS[box.maxclass]['patching_rect']
                rect = x, y, w, dh
            else:
                h = self._layout_mgr.box_height
                rect = x, y, w, h
        # rect = x, y, self._layout_mgr.box_width, self._layout_mgr.box_height 
        if comment_pos:
            assert comment_pos in ["above", "below", "right", "left"], f"comment:{comment} / comment_pos: {comment_pos}"
            patching_rect = getattr(self._layout_mgr, comment_pos)(rect)
        else:
            patching_rect = self._layout_mgr.above(rect)
        if comment_pos == "left": # special case
            self.add_comment(comment, patching_rect, justify="right")
        else:
            self.add_comment(comment, patching_rect)

    def add_patchline_by_index(
        self, src_id: str, dst_id: str, dst_inlet: int = 0, src_outlet: int = 0
    ):
        """Patchline creation between two objects using stored indexes"""

        src_id = self._objects[src_id]
        dst_id = self._objects[dst_id]
        self.add_patchline(src_id, src_outlet, dst_id, dst_inlet)

    def add_patchline(self, src_id: str, src_outlet: int, dst_id: str, dst_inlet: int):
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
        self._lines.append(patchline)
        self._edge_ids.append((src_id, dst_id))
        return patchline

    def add_line(self, src_obj, dst_obj, inlet=0, outlet=0):
        """convenience line adding taking objects with default outlet to inlet"""

        return self.add_patchline(src_obj.id, outlet, dst_obj.id, inlet)

    # alias for add_line
    link = add_line

    def add_textbox(
        self,
        text: str,
        maxclass: str = None,
        numinlets: int = None,
        numoutlets: int = None,
        outlettype: list[str] = None,
        patching_rect: list[float] = None,
        id: str = None,
        comment: str = None,
        comment_pos: str = None,
        **kwds,
    ):
        """Add a generic textbox object to the patcher.

        Looks up default attributes from a dictionary.
        """
        _maxclass, *tail = text.split()
        if _maxclass in MAXCLASS_DEFAULTS and not maxclass:
            maxclass = _maxclass
            # _defaults = MAXCLASS_DEFAULTS[_maxclass]
            # if "patching_rect" in _defaults and not patching_rect:
            #     patching_rect = _defaults["patching_rect"]

        if self.classnamespace == "rnbo":
            kwds["rnbo_classname"] = _maxclass
            if _maxclass in ["codebox", "codebox~"]:
                if "code" in kwds:
                    kwds["code"] = kwds["code"].replace("\n", "\r\n")
                    kwds["rnbo_extra_attributes"] = dict(
                        code=kwds["code"],
                        hot=0,
                    )

        return self.add_box(
            Box(
                id=id or self.get_id(),
                text=text,
                maxclass=maxclass or "newobj",
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 0,
                outlettype=outlettype or [""],
                patching_rect=patching_rect or self.get_pos(maxclass)
                if maxclass
                else self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def _add_float(self, value, *args, **kwds):
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
        else:
            raise ValueError(
                "should be: .add(<float>, '<name>') OR .add(<float>, name='<name>')"
            )

    def _add_int(self, value, *args, **kwds):
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
        else:
            raise ValueError(
                "should be: .add(<int>, '<name>') OR .add(<int>, name='<name>')"
            )

    def _add_str(self, value, *args, **kwds):
        """type-handler for str values in `add`"""

        assert isinstance(value, str)

        maxclass, *text = value.split()
        text = " ".join(text)

        # first check _maxclass_methods
        # these methods don't need the maxclass, just the `text` tail of value
        if maxclass in self._maxclass_methods:
            return self._maxclass_methods[maxclass](text, **kwds)
        # next two require value as a whole
        elif maxclass == "p":
            return self.add_subpatcher(value, **kwds)
        elif maxclass == "gen~":
            return self.add_gen(value, **kwds)
        elif maxclass == "rnbo~":
            return self.add_rnbo(value, **kwds)
        else:
            return self.add_textbox(text=value, **kwds)

    def add(self, value, *args, **kwds):
        """generic adder: value can be a number or a list or text for an object."""

        if isinstance(value, float):
            return self._add_float(value, *args, **kwds)

        elif isinstance(value, int):
            return self._add_int(value, *args, **kwds)

        elif isinstance(value, str):
            return self._add_str(value, *args, **kwds)

        else:
            raise NotImplementedError

    def add_codebox(
        self,
        code: str,
        patching_rect: list[float] = None,
        id: str = None,
        comment: str = None,
        comment_pos: str = None,
        tilde=False,
        **kwds,
    ):
        """Add a codebox."""

        _maxclass = "codebox~" if tilde else "codebox"
        _code = code.replace("\n", "\r\n")

        if self.classnamespace == "rnbo":
            kwds["rnbo_classname"] = _maxclass
            kwds["rnbo_extra_attributes"] = dict(
                code=_code,
                hot=0,
            )

        return self.add_box(
            Box(
                id=id or self.get_id(),
                code=_code,
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
        patching_rect: list[float] = None,
        id: str = None,
        comment: str = None,
        comment_pos: str = None,
        **kwds,
    ):
        """Add a codebox_tilde"""
        return self.add_codebox(
            code, patching_rect, id, comment, comment_pos, tilde=True, **kwds
        )

    def add_message(
        self,
        text: str = None,
        patching_rect: list[float] = None,
        id: str = None,
        comment: str = None,
        comment_pos: str = None,
        **kwds,
    ):
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
        self, text: str, patching_rect: list[float] = None, id: str = None, justify: str = None, **kwds
    ):
        """Add a basic comment object."""
        if justify:
            kwds['textjustification'] = {
                'left':   0,
                'center': 1,
                'right':  2
            }[justify]
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
        comment: str = None,
        comment_pos: str = None,
        patching_rect: list[float] = None,
        id: str = None,
        **kwds,
    ):
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
        comment: str = None,
        comment_pos: str = None,
        patching_rect: list[float] = None,
        id: str = None,
        **kwds,
    ):
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
        initial: float = None,
        minimum: float = None,
        maximum: float = None,
        shortname: str = None,
        id: str = None,
        rect: list[float] = None,
        hint: str = None,
        comment: str = None,
        comment_pos: str = None,
        **kwds,
    ):
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
        initial: int = None,
        minimum: int = None,
        maximum: int = None,
        shortname: str = None,
        id: str = None,
        rect: list[float] = None,
        hint: str = None,
        comment: str = None,
        comment_pos: str = None,
        **kwds,
    ):
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

    def add_subpatcher(
        self,
        text: str,
        maxclass: str = None,
        numinlets: int = None,
        numoutlets: int = None,
        outlettype: list[str] = None,
        patching_rect: list[float] = None,
        id: str = None,
        patcher: "Patcher" = None,
        **kwds,
    ):
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
        return self.add_subpatcher(
            text, patcher=Patcher(parent=self, classnamespace="rnbo"), **kwds
        )

    def add_coll(
        self,
        name: str = None,
        dictionary: dict = None,
        embed: int = 1,
        patching_rect: list[float] = None,
        text: str = None,
        id: str = None,
        comment: str = None,
        comment_pos: str = None,
        **kwds,
    ):
        """Add a coll object with option to pre-populate from a py dictionary."""
        extra = {"saved_object_attributes": {"embed": embed, "precision": 6}}
        if dictionary:
            extra["coll_data"] = {
                "count": len(dictionary.keys()),
                "data": [{"key": k, "value": v} for k, v in dictionary.items()],
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
        name: str = None,
        dictionary: dict = None,
        embed: int = 1,
        patching_rect: list[float] = None,
        text: str = None,
        id: str = None,
        comment: str = None,
        comment_pos: str = None,
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
        name: str = None,
        array: list[int] = None,
        embed: int = 1,
        patching_rect: list[float] = None,
        text: str = None,
        id: str = None,
        comment: str = None,
        comment_pos: str = None,
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
        name: str = None,
        array: list[int] = None,
        embed: int = 1,
        patching_rect: list[float] = None,
        text: str = None,
        id: str = None,
        comment: str = None,
        comment_pos: str = None,
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
        name: str = None,
        array: list[int] = None,
        patching_rect: list[float] = None,
        text: str = None,
        id: str = None,
        comment: str = None,
        comment_pos: str = None,
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
        prefix: str = None,
        autopopulate: int = 1,
        items: list[str] = None,
        patching_rect: list[float] = None,
        depth: int = None,
        id: str = None,
        comment: str = None,
        comment_pos: str = None,
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
        outlettype: list[str] = None,
        bgmode: int = 0,
        border: int = 0,
        clickthrough: int = 0,
        enablehscroll: int = 0,
        enablevscroll: int = 0,
        lockeddragscroll: int = 0,
        offset: list[float] = None,
        viewvisibility: int = 1,
        patching_rect: list[float] = None,
        id: str = None,
        comment: str = None,
        comment_pos: str = None,
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


class Box:
    """Max Box object"""

    def __init__(
        self,
        maxclass: str = None,
        numinlets: int = None,
        numoutlets: int = None,
        id: str = None,
        patching_rect: list[float] = None,
        **kwds,
    ):
        self.id = id
        self.maxclass = maxclass or "newobj"
        self.numinlets = numinlets or 0
        self.numoutlets = numoutlets or 1
        # self.outlettype = outlettype
        self.patching_rect = patching_rect or [0, 0, 62, 22]

        self._kwds = self._remove_none_entries(kwds)
        self._patcher = self._kwds.pop("patcher", None)
        # self._parse(self.text)

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
        box = cls()
        box.__dict__.update(obj_dict)
        if hasattr(box, "patcher"):
            box._patcher = Patcher.from_dict(getattr(box, "patcher"))
        return box

    @property
    def oid(self) -> int:
        return int(self.id[4:])

    @property
    def subpatcher(self):
        return self._patcher


class Patchline:
    """A class for Max patchlines."""

    def __init__(self, source: list = None, destination: list = None, **kwds):
        self.source = source or []
        self.destination = destination or []
        self._kwds = kwds

    def __repr__(self):
        return f"Patchline({self.source} -> {self.destination})"

    @property
    def src(self):
        return self.source[0]

    @property
    def dst(self):
        return self.destination[0]

    def to_tuple(self):
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
    def from_dict(cls, obj_dict):
        patchline = cls()
        patchline.__dict__.update(obj_dict)
        return patchline
