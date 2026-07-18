from pathlib import Path

import pytest
from py2max import Patcher

DATA_DIR = Path(__file__).parent / "data"

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from scipy import signal

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def test_table():
    p = Patcher("outputs/test_table.maxpat")
    table = p.add_table("bob", array=list(range(128)))
    p.save()

    assert len(p._boxes) == 1
    assert table.maxclass == "newobj"
    assert table.text == "table bob @embed 1"

    d = table.to_dict()["box"]
    assert d["embed"] == 1
    assert d["saved_object_attributes"]["name"] == "bob"
    assert d["saved_object_attributes"]["size"] == 128
    assert d["table_data"] == list(range(128))


def test_table_tilde():
    p = Patcher("outputs/test_table_tilde.maxpat")
    table = p.add_table_tilde("bob", array=list(range(128)))
    p.save()

    assert len(p._boxes) == 1
    assert table.maxclass == "newobj"
    assert table.text == "table~ bob @embed 1"

    d = table.to_dict()["box"]
    assert d["embed"] == 1
    assert d["saved_object_attributes"]["name"] == "bob"
    assert d["saved_object_attributes"]["size"] == 128
    assert d["table_data"] == list(range(128))


@pytest.mark.skipif(not HAS_NUMPY, reason="needs numpy to be installed")
def test_table_wavetable1():
    length = 128
    t = np.linspace(0, 1, length, endpoint=False)
    # arr = signal.square(np.pi * 2 * t)
    arr = np.sin(t * 3) * length
    p = Patcher.from_file(DATA_DIR / "tabular.maxpat")

    table_index, table = p.find_box_with_index("table~")
    table.table_data = list(arr)
    p._boxes[table_index] = table

    itable_index, itable = p.find_box_with_index("itable")
    itable.table_data = list(arr)
    p._boxes[itable_index] = itable

    p.save_as("outputs/test_table_wavetable1.maxpat")

    assert "table~" in table.text
    assert table.to_dict()["box"]["table_data"] == list(arr)
    assert itable.maxclass == "itable"
    assert itable.to_dict()["box"]["table_data"] == list(arr)


@pytest.mark.skipif(
    not (HAS_NUMPY and HAS_SCIPY), reason="needs numpy and scipy to be installed"
)
def test_table_wavetable2():
    length = 128
    t = np.linspace(0, 1, length, endpoint=False)
    arr = signal.square(np.pi * 2 * t) * length
    # arr = np.sin(t * 5) * length
    p = Patcher.from_file(DATA_DIR / "tabular.maxpat")

    table = p.find_box("table~")
    table.table_data = list(arr)
    # p._objects[table.id] = table

    itable = p.find_box("itable")
    itable.table_data = list(arr)
    # p._objects[itable.id] = itable

    p.save_as("outputs/test_table_wavetable2.maxpat")

    assert "table~" in table.text
    assert table.to_dict()["box"]["table_data"] == list(arr)
    assert itable.maxclass == "itable"
    assert itable.to_dict()["box"]["table_data"] == list(arr)
