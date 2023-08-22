import pytest
from py2max import Patcher

try:
    import numpy as np
    # from scipy import signal
    HAS_NUMPY=True
except ImportError:
    HAS_NUMPY=False



def test_table():
    p = Patcher('outputs/test_table.maxpat')
    p.add_table('bob', array=list(range(128)))
    p.save()


def test_table_tilde():
    p = Patcher('outputs/test_table_tilde.maxpat')
    p.add_table_tilde('bob', array=list(range(128)))
    p.save()


@pytest.mark.skipif(not HAS_NUMPY, reason="needs numpy and scipy to be installed")
def test_table_wavetable():
    length = 128
    t = np.linspace(0, 1, length, endpoint=False)
    # arr = signal.square(np.pi * 2 * t)
    arr = np.sin(t * 3) * length
    p = Patcher.from_file("tests/data/tabular.maxpat")
    
    table_index, table = p.find_box('table~')
    table.table_data = list(arr)
    p._boxes[table_index] = table

    itable_index, itable = p.find_box("itable")
    itable.table_data = list(arr)
    p._boxes[itable_index] = itable

    p.save_as("outputs/test_table_wavetable.maxpat")






if __name__ == '__main__':
    test_table()
    test_table_tilde()
