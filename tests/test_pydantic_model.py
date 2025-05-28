from pathlib import Path
from typing import Literal, Optional, Annotated, TypeAlias

import pytest

try:
    from pydantic import BaseModel, ConfigDict, Field, ValidationError

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
        name: str
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
    tb1 = TextBox(id=2, name="tb1", text="nice one")
    p = Patcher(name="my_patcher", boxes=[b1, tb1])
    json_file = "outputs/test_pydantic_model.json"
    json_file2 = "outputs/test_pydantic_model2.json"
    p.save(json_file)
    p1 = Patcher.from_file(json_file, save_to=json_file2)
