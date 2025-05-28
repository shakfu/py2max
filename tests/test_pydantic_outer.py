from collections import defaultdict
from pathlib import Path
from typing import Literal, Annotated, TypeAlias, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_serializer,
    field_validator,
    model_validator,
    ValidationError,
)

class BaseBox(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=True)
    box_type: Literal["box"] = "box"

class TextBox(BaseBox):
    box_type: Literal["textbox"] = "textbox"
    value: str

class FloatBox(BaseBox):
    box_type: Literal["floatbox"] = "floatbox"
    value: float = 0.0

class IntBox(BaseBox):
    box_type: Literal["intbox"] = "intbox"
    value: int = 0

BoxType: TypeAlias = Union[
    BaseBox,
    TextBox,
    FloatBox,
    IntBox,
]

class Box(BaseModel):
    box: Annotated[BoxType, Field(discriminator="box_type")]

class Container(BaseModel):
    name: str
    boxes: list[Box]

    @classmethod
    def from_file(cls, path: str | Path, save_to: str | Path = None) -> "Container":
        with open(path, encoding="utf8") as f:
            container = cls.model_validate_json(f.read())
        if save_to:
            container.save(save_to)
        return container

    def save(self, path: str | Path):
        with open(path, "w", encoding="utf8") as f:
            f.write(self.model_dump_json(indent=4))

def test_pydantic_outer():
    tb1 = TextBox(value="nice one")
    fb1 = FloatBox(value=1.2)
    ib1 = IntBox(value=10)

    b1 = Box(box=tb1)
    b2 = Box(box=fb1)
    b3 = Box(box=ib1)

    c1 = Container(name="c1", boxes=[b1, b2, b3])
    json_file = "outputs/test_pydantic_outer.json"
    json_file2 = "outputs/test_pydantic_outer2.json"
    c1.save(json_file)
    c2 = Container.from_file(json_file, save_to=json_file2)
    with open(json_file) as f:
        with open(json_file2) as g:
            assert f.read() == g.read()


