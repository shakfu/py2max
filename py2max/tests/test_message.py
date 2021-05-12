
from .. import Patcher


def test_message():
    p = Patcher('outputs/test_message.maxpat')
    p.add_message('a b c d')
    p.save()


if __name__ == '__main__':
    test_message()
