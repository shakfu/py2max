"""a sketch of an alternative design for py2max

Each object has:
    - an inner model dict
    - property-based access to that model dict
    - specialized classes to differentiate between Box Types

"""
import json
from typing import NamedTuple, Union, Optional
from pathlib import Path


class Rect(NamedTuple):
    x: float
    y: float
    w: float
    h: float


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
    def __init__(self, source: tuple[str, int], destination: tuple[str, int], order: int):
        src_id, src_outlet = source
        dst_id, dst_inlet = destination
        self._model = {
            "source": (src_id, src_outlet),
            "destination": (dst_id, dst_inlet),
            "order": order,
        }

    def __repr__(self):
        return f"Patchline({self.source} -> {self.destination})"

    @classmethod
    def from_dict(cls, obj_dict: dict):
        """convert to `Patchline` object from dict"""
        patchline = cls()
        patchline._model.update(obj_dict)
        return patchline

    def to_dict(self):
        """create dict from object with extra kwds included"""
        d = self._model.copy()
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
        # layout: str = "horizontal",
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
        # self._layout_mgr: LayoutManager = self.set_layout_mgr(layout)
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
            "rect": [85.0, 104.0, 640.0, 480.0],
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

    def _get_id(self) -> str:
        """helper func to increment object ids"""
        self._id_counter += 1
        return f"obj-{self._id_counter}"

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

    def add_textbox(
        self,
        text: str,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[list[str]] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds,
    ) -> TextBox:
        """Add a generic textbox object to the patcher.

        Looks up default attributes from a dictionary.
        """

        tbox = TextBox(
            id=id or self._get_id(),
            text=text,
            maxclass=maxclass or "newobj",
            numinlets=numinlets or 1,
            numoutlets=numoutlets or 0,
            patching_rect=patching_rect,
            outlettype=outlettype or [""],
            **kwds,
        )
        self.boxes.append(tbox)
        return tbox

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
    p.save()
