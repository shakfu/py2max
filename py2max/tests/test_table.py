
from .. import Patcher


def test_table():
    p = Patcher('outputs/test_table.maxpat')
    p.add_table('bob', array=list(range(128)))
    p.save()


if __name__ == '__main__':
    test_table()
