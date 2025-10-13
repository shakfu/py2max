from py2max import Patcher
from py2max.utils import pitch2freq

# Create patcher with layout
p = Patcher(
    "outputs/test_tutorial_simple_synthesis.maxpat",
    layout="matrix",
)

# Create oscillators for a C major chord
freqs = [pitch2freq("C4"), pitch2freq("E4"), pitch2freq("G4")]
oscillators = []

for i, freq in enumerate(freqs):
    osc = p.add_textbox(f"cycle~ {freq:.2f}")
    oscillators.append(osc)

# Add gain controls
gain_mults = []
for i in range(3):
    gain_param = p.add_floatparam(f"gain{i}", initial=0.3)
    gain_mult = p.add_textbox("*~")
    gain_mults.append(gain_mult)
    # Connect parama and oscillator to gain_mult
    p.add_line(gain_param, gain_mult)
    p.add_line(oscillators[i], gain_mult, inlet=1)


# Add master volume and output
master_vol = p.add_floatparam("master", inital=0.5)
master_mult = p.add_textbox("*~")
output = p.add_textbox("ezdac~")

for gain_mult in gain_mults:
    # mix the input signals
    p.add_line(gain_mult, master_mult)

p.add_line(master_vol, master_mult, inlet=1)
p.add_line(master_mult, output)
p.add_line(master_mult, output, inlet=1)

# Optimize layout
p.optimize_layout()
p.save()
