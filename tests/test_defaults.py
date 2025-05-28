from py2max import Patcher


def test_defaults():
    p = Patcher(path="outputs/test_defaults.maxpat")
    for i in range(10):
        p.add(f"cycle~ {i * 20}")
    p.add_box("filtergraph~")
    p.add_box("scope~")
    p.add_box("ezdac~")
    p.save()
