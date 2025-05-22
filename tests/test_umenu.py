from py2max import Patcher


def test_umenu():
    p = Patcher("outputs/test_umenu.maxpat")
    p.add_umenu(items=["01.wav", "02.wav", "03.wav"])
    p.save()


if __name__ == "__main__":
    test_umenu()
