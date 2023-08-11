from py2max import Patcher


def test_patcher_from_file():
    p = Patcher.from_file('tests/data/demo.maxpat', save_to='outputs/test_patcher.maxpat')

    p.save()


if __name__ == '__main__':
    test_patcher_from_file()
