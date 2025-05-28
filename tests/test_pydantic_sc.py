from pathlib import Path
from collections import defaultdict
from typing import (
    Literal,
    Optional,
    Annotated,
    TypeAlias,
    Union,
)

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

        id: int
        text: Optional[str] = None
        maxclass: Literal["newobj"] = "newobj"
        numinlets: int = 0
        numoutlets: int = 1
        patcher: Optional["Patcher"] = None

        # @field_validator("text")
        # def text_is_valid(cls, value: str):
        #     """Exclude 'text' field in export if it is None"""
        #     if value is None:
        #         raise Exception
        #     return str(value)

        # @model_serializer
        # def serialize_box(self):
        #     """Custom serialization of Box object"""
        #     box = {}
        #     for f in self.__class__.model_fields:
        #         val = getattr(self, f)
        #         if val is not None:
        #             box[f] = val
        #     box.update(self.__pydantic_extra__)
        #     return dict(box=box)

        @model_validator(mode="before")
        def validate_box(cls, data: dict) -> dict:
            """Customize export from 'dict_result -> dict(box=dict_result)'"""
            result = defaultdict(dict, data)
            if "box" in result:
                return dict(result["box"])
            else:
                return dict(data)

    class Message(Box):
        maxclass: Literal["message"] = "message"
        numinlets: int = 2
        numoutlets: int = 1

    class Float(Box):
        maxclass: Literal["flonum"] = "flonum"
        numinlets: int = 1
        numoutlets: int = 2

    class Int(Box):
        maxclass: Literal["number"] = "number"
        numinlets: int = 1
        numoutlets: int = 2

    MaxClass: TypeAlias = Union[
        Box,
        Message,
        Float,
        Int,
    ]

    class Patcher(BaseModel):
        boxes: list[Annotated[MaxClass, Field(discriminator="maxclass")]]

        @classmethod
        def from_file(
            cls, path: str | Path, save_to: Optional[str | Path] = None
        ) -> "Patcher":
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

    b1 = Box(id=1, name="b1")
    tb1 = Message(id=2, name="tb1", text="nice one")
    p = Patcher(boxes=[b1, tb1])
    json_file = "outputs/test_pydantic_sc.json"
    json_file2 = "outputs/test_pydantic_sc2.json"
    p.save(json_file)
    p1 = Patcher.from_file(json_file, save_to=json_file2)
