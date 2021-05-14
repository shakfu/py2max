
from .. import Patcher


def test_zl_group():
    p = Patcher('outputs/test_zl_group.maxpat')
    lst = p.add_message('1 2 2 3 4 3 4 5 6 7 7 8 8 9 9 10')
    zlg = p.add_textbox('zl.group 2')
    out = p.add_textbox('print group')
    p.link(lst, zlg)
    p.link(zlg, out)
    p.save()


if __name__ == '__main__':
    test_zl_group()
