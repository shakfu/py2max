
from .. import Patcher


def test_add():
    p = Patcher('outputs/test_add.maxpat')
    # float param
    p.add(10.2, "param1")
    p.add(0.56, name="param2")
    # floatbox
    p.add(1.2)

    # int param
    p.add(10, "param3")
    p.add(56, name="param4")
    # intbox
    p.add(2)

    # message
    p.add('m hello')

    # comment
    p.add('c my comment')

    # textbox
    p.add('cycle~ 440')

    # subpatcher
    box = p.add('p mysub')
    assert box.subpatcher

    # gen~
    gen = p.add('gen~')
    assert gen.subpatcher

    # coll
    p.add('coll', dictionary=dict(a=1, b=2))

    # dict
    p.add('dict', dictionary=dict(a=1, b=2))

    # table & itable
    p.add('table', array=list(range(128)))
    p.add('itable', array=list(range(128)))

    # umenu
    p.add('umenu', items=['a','b', 'c'])

    # bpatcher
    p.add('bpatcher bp.LFO.maxpat', extract=1)

    p.save()


if __name__ == '__main__':
    test_add()
