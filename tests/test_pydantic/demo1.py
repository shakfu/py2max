from pydantic import BaseModel
from typing import Dict, Literal, Union

class MainClass(BaseModel):
    x: int

class SubclassA(MainClass):
    a: int
    type: Literal['A'] = 'A'

class SubclassB(MainClass):
    b: int
    type: Literal['B'] = 'B'

class MyCatalog(BaseModel):
    stuff: Dict[str, Union[SubclassA, SubclassB]]

if __name__=='__main__':

    cat = MyCatalog(stuff={})
    cat.stuff['item1'] = SubclassA(x=0, a=1)
    cat.stuff['item2'] = SubclassB(x=0, b=1)

    exported = cat.model_dump_json()
    imported = MyCatalog.model_validate_json(exported)

    print(cat)
    print(cat.model_dump())
    print(cat.model_dump_json())
    print(imported)

