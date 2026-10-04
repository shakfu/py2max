from py2max import Patcher
from py2max.utils import object_name


def test_basic(tmp_path):
    path = tmp_path / "test_basic.maxpat"
    p = Patcher(str(path))
    osc1 = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")
    p.add_line(osc1, gain)
    p.add_line(gain, dac)
    p.save()

    # Structure is as built.
    assert len(p._boxes) == 3
    assert len(p._lines) == 2
    assert [object_name(b) for b in p._boxes] == ["cycle~", "gain~", "ezdac~"]
    assert [b.text for b in p._boxes] == ["cycle~ 440", "", ""]

    # Saving then loading preserves the structure (round-trip fidelity).
    reloaded = Patcher.from_file(str(path))
    assert len(reloaded._boxes) == 3
    assert len(reloaded._lines) == 2
    assert [b.text for b in reloaded._boxes] == ["cycle~ 440", "", ""]
    assert [b.maxclass for b in reloaded._boxes] == ["newobj", "gain~", "ezdac~"]
