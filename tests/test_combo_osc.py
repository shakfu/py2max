from py2max import Patcher


def pitch2freq(pitch, A4=440):
    """
    from: https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e#file-note_to_freq-py
    """
    notes = ['A', 'Bb', 'B', 'C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab']
    note = notes.index(pitch[:-1])
    octave = int(pitch[-1])
    distance_from_A4 = note + 12 * (octave - (4 if note < 3 else 5))
    return A4 * 2 ** (distance_from_A4/12)

def pitched_osc(p, pitch):
    freq = pitch2freq(pitch)
    return p.add_textbox(f"cycle~ {freq}")


def test_combo_osc():
    p = Patcher("outputs/test_combo_osc.maxpat", layout="vertical")
    osc = pitched_osc(p, "C3")
    dac = p.add_textbox("ezdac~")
    p.link(osc, dac)
    p.save()
