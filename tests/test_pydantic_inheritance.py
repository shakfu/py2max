from typing import Literal, Annotated, TypeAlias

import pytest

try:
    from pydantic import BaseModel, ConfigDict, Field, model_serializer

    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False


@pytest.mark.skipif(not HAS_PYDANTIC, reason="requires pydantic")
def test_pydantic():
    class Box(BaseModel):
        model_config = ConfigDict(extra="allow")
        id: int
        name: str
        maxclass: Literal["box"] = "box"

    class TextBox(Box):
        maxclass: Literal["textbox"] = "textbox"
        text: str

    MaxClass: TypeAlias = Box | TextBox

    class Patcher(BaseModel):
        boxes: list[Annotated[MaxClass, Field(discriminator="maxclass")]]

    b1 = Box(id=1, name="b1")
    tb1 = TextBox(id=2, name="tb1", text="nice one")
    p = Patcher(boxes=[b1, tb1])
