import pytest
from typing import NamedTuple, Optional, Dict

try:
    from pydantic import BaseModel, ConfigDict, model_serializer
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False

def test_pydantic():
    class Rect(NamedTuple):
        x: float
        y: float
        w: float
        h: float


    class Box(BaseModel):
        model_config = ConfigDict(extra='allow')

        id: str
        text: str
        maxclass: str = "newobj"
        numinlets: int = 0
        numoutlets: int = 1
        outlettype: list[str] = [""]
        patching_rect: Rect = Rect(x=0, y=0, w=62, h=22)
        patcher: Optional['Patcher'] = None

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
        model_config = ConfigDict(extra='allow')

        source: tuple[str, int]
        destination: tuple[str, int]
        order: int

        @model_serializer
        def serialize_box(self):
            line = {}
            for f in self.model_fields:
                line[f] =  getattr(self, f)
            line.update(self.__pydantic_extra__)
            return dict(patchline=line)


    class Patcher(BaseModel):
        model_config = ConfigDict(extra='allow')

        title: str
        boxes: list[Box] = []
        lines: list[Patchline] = []

        @model_serializer
        def serialize_box(self):
            patcher = {}
            for f in self.model_fields:
                val = getattr(self, f)
                if val is not None:
                    patcher[f] = val
            patcher.update(self.__pydantic_extra__)
            return dict(patcher=patcher)

    b1 = Box(id="osc", text="cycle~ 440")
    b2 = Box(id="dac", text="ezdac~")

    l1 = Patchline(source=("osc", 0), destination=("dac", 0), order=0)
    l2 = Patchline(source=("osc", 0), destination=("dac", 1), order=1)

    p = Patcher(title='top')
    p.boxes.append(b1)
    p.boxes.append(b2)
    p.lines.append(l1)
    p.lines.append(l2)

    with open('outputs/test_pydantic.maxpat', 'w') as f:
        f.write(p.model_dump_json(indent=4))
