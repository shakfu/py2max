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
    def __init__(self, **kwds):
        self._model = {}
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


class TextBox(Box):
    @property
    def text(self):
        assert "text" in self._model, "`text` field must be in `model`"
        return self._model["text"]

    @text.setter
    def text(self, value: str):
        self._model["text"] = value


class Patchline:
    def __init__(self, src_id: str, dst_id: str, src_outlet: int = 0, dst_inlet: int = 0, order: int = 0):
        self._model = {
            "source": [src_id, src_inlet],
            "destination": [dst_id, dst_inlet],
            "order": order,
        }

    def __repr__(self):
        return f"Patchline({self.src_id} -> {self.dst_id})"

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


class Patcher:
    def __init__(self, path: str | Path = None, parent: Optional[Box] = None):
        self._path = path
        self._parent = parent
        self._reset_on_render = True
        self._model = {}
        self.boxes = []
        self.lines = []

    def __repr__(self):
        return f"{self.__class__.__name__}(path='{self._path}')"

    @classmethod
    def from_dict(cls, patcher_dict: dict, save_to: Optional[str] = None) -> "Patcher":
        """create a patcher instance from a dict"""

        if save_to:
            patcher = cls(save_to)
        else:
            patcher = cls()
        patcher._model.update(patcher_dict)

        for box_dict in patcher._model["boxes"]:
            if "text" in box_dict['box']:
                box = TextBox.from_dict(box_dict['box'])
            else:
                box = Box.from_dict(box_dict['box'])
            patcher.boxes.append(box)

        for line_dict in patcher._model["lines"]:
            line = Patchline.from_dict(line_dict)
            patcher.lines.append(line)

        return patcher

    @classmethod
    def from_file(cls, path: Union[str, Path], save_to: Optional[str] = None) -> "Patcher":
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
    p = Patcher.from_file("../data/nested.maxpat", save_to="out.maxpat")
    p.save()
