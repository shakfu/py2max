
from .. import Patcher


def test_itable():
    p = Patcher('outputs/test_itable.maxpat')
    p.add_itable('bob', array=list(range(128)))
    p.save()


if __name__ == '__main__':
    test_itable()
