import pytest
pytest.skip(allow_module_level=True)

from typing import NamedTuple, Optional, Dict

try:
    from pydantic import BaseModel, ConfigDict, model_serializer

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

@pytest.mark.skipif(not HAS_PYDANTIC, reason="requires pydantic")
def test_pydantic():
    class Rect(NamedTuple):
        x: float
        y: float
        w: float
        h: float

    class Box(BaseModel):
        model_config = ConfigDict(extra="allow")

        id: str
        text: str
        maxclass: str = "newobj"
        numinlets: int = 0
        numoutlets: int = 1
        outlettype: list[str] = [""]
        patching_rect: Rect = Rect(x=0, y=0, w=62, h=22)
        patcher: Optional["Patcher"] = None

        @model_serializer
        def serialize_box(self):
            box = {}
            for f in self.model_fields:
                val = getattr(self, f)
                if val is not None:
                    box[f] = val
            box.update(self.__pydantic_extra__)
            return dict(box=box)

    class Patchline(BaseModel):
        model_config = ConfigDict(extra="allow")

        source: tuple[str, int]
        destination: tuple[str, int]
        order: int

        @model_serializer
        def serialize_box(self):
            line = {}
            for f in self.model_fields:
                line[f] = getattr(self, f)
            line.update(self.__pydantic_extra__)
            return dict(patchline=line)

    class Patcher(BaseModel):
        model_config = ConfigDict(extra="allow")

        title: str
        fileversion: int = 1
        appversion: dict = {
            "major": 8,
            "minor": 5,
            "revision": 5,
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

        _id_count: int = 0
        _link_count: int = 0

        @model_serializer
        def serialize_box(self):
            patcher = {}
            for f in self.model_fields:
                val = getattr(self, f)
                if val is not None:
                    patcher[f] = val
            patcher.update(self.__pydantic_extra__)
            return dict(patcher=patcher)

        def add(
            self,
            text: str,
            maxclass: str = "newobj",
            numinlets: int = 0,
            numoutlets: int = 1,
            outlettype: list[str] = [""],
            patching_rect: Rect = Rect(x=0, y=0, w=62, h=22),
            patcher: Optional["Patcher"] = None,
            **kwds,
        ):
            self._id_count += 1
            box = Box(
                text=text,
                id=str(self._id_count),
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

        def link(self, src: Box, dst: Box, outlet=0, inlet=0):
            self._link_count += 1
            line = Patchline(
                source=(src.id, outlet),
                destination=(dst.id, inlet),
                order=self._link_count,
            )
            self.lines.append(line)

    p = Patcher(title="top")
    osc = p.add("cycle~ 440")
    dac = p.add("ezdac~")
    p.link(osc, dac)
    p.link(osc, dac, inlet=1)

    with open("outputs/test_pydantic_concept.maxpat", "w") as f:
        f.write(p.model_dump_json(indent=4))


