import pytest
from py2max import Patcher

try:
    import numpy as np
    HAS_NUMPY=True
except ImportError:
    HAS_NUMPY=False

try:
    from scipy import signal
    HAS_SCIPY=True
except ImportError:
    HAS_SCIPY=False



def test_table():
    p = Patcher(path='outputs/test_table.maxpat')
    p.add_table('bob', array=list(range(128)))
    p.save()


def test_table_tilde():
    p = Patcher(path='outputs/test_table_tilde.maxpat')
    p.add_table_tilde('bob', array=list(range(128)))
    p.save()


@pytest.mark.skipif(not HAS_NUMPY, reason="needs numpy to be installed")
def test_table_wavetable1():
    length = 128
    t = np.linspace(0, 1, length, endpoint=False)
    # arr = signal.square(np.pi * 2 * t)
    arr = np.sin(t * 3) * length
    p = Patcher.from_file("tests/data/tabular.maxpat")
    
    table_index, table = p.find_box_with_index('table~')
    table.table_data = list(arr)
    p.boxes[table_index] = table

    itable_index, itable = p.find_box_with_index("itable")
    itable.table_data = list(arr)
    p.boxes[itable_index] = itable

    p.save_as("outputs/test_table_wavetable1.maxpat")


@pytest.mark.skipif(not (HAS_NUMPY and HAS_SCIPY), reason="needs numpy and scipy to be installed")
def test_table_wavetable2():
    length = 128
    t = np.linspace(0, 1, length, endpoint=False)
    arr = signal.square(np.pi * 2 * t) * length
    # arr = np.sin(t * 5) * length
    p = Patcher.from_file("tests/data/tabular.maxpat")
    
    table = p.find('table~')
    table.table_data = list(arr)
    # p._objects[table.id] = table

    itable = p.find("itable")
    itable.table_data = list(arr)
    # p._objects[itable.id] = itable

    p.save_as("outputs/test_table_wavetable2.maxpat")


