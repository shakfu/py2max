
from py2max import Patcher


def test_message():
    p = Patcher(path='outputs/test_message.maxpat')
    p.add_message('a b c d')
    p.save()

