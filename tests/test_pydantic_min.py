from collections import defaultdict
from pathlib import Path
from typing import Literal, Annotated, TypeAlias, Union

import pytest

try:
    from pydantic import (
        BaseModel,
        ConfigDict,
        Field,
        model_serializer,
        field_validator,
        model_validator,
        ValidationError,
    )

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False


@pytest.mark.skipif(not HAS_PYDANTIC, reason="requires pydantic")
def test_pydantic():
    class Box(BaseModel):
        model_config = ConfigDict(extra="allow", validate_assignment=True)
        box_type: Literal["box"] = "box"

        # @model_serializer
        # def serialize_box(self):
        #     box = {}
        #     for f in self.__class__.model_fields:
        #         val = getattr(self, f)
        #         if val is not None:
        #             box[f] = val
        #     box.update(self.__pydantic_extra__)
        #     return dict(box=box)

        # @model_validator(mode="before")
        # def validate_box(cls, data: dict) -> dict:
        #     result = defaultdict(dict, data)
        #     if "box" in result:
        #         return dict(result["box"])
        #     else:
        #         return dict(data)

    class TextBox(Box):
        box_type: Literal["textbox"] = "textbox"
        value: str

    class FloatBox(Box):
        box_type: Literal["floatbox"] = "floatbox"
        value: float = 0.0

    class IntBox(Box):
        box_type: Literal["intbox"] = "intbox"
        value: int = 0

    BoxType: TypeAlias = Union[
        Box,
        TextBox,
        FloatBox,
        IntBox,
    ]

    class Container(BaseModel):
        name: str
        boxes: list[Annotated[BoxType, Field(discriminator="box_type")]]

        @classmethod
        def from_file(
            cls, path: str | Path, save_to: str | Path = None
        ) -> "Container":
            with open(path, encoding="utf8") as f:
                patcher = cls.model_validate_json(f.read())
            if save_to:
                patcher.save(save_to)
            return patcher

        def save(self, path: str | Path):
            """save as .maxpat json file"""
            path = Path(path)
            if path.parent:
                path.parent.mkdir(exist_ok=True)
            with open(path, "w", encoding="utf8") as f:
                f.write(self.model_dump_json(indent=4))

    tb1 = TextBox(value="nice one")
    fb1 = FloatBox(value=1.2)
    ib1 = IntBox(value=10)
    c1 = Container(name="c1", boxes=[tb1, fb1, ib1])
    json_file = "outputs/test_pydantic_min.json"
    json_file2 = "outputs/test_pydantic_min2.json"
    c1.save(json_file)
    p1 = Container.from_file(json_file, save_to=json_file2)
