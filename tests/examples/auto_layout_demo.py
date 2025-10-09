"""Demonstration of auto-layout feature using WebCola in the interactive editor.

This script creates a complex Max patch with randomly positioned objects,
then you can use the "Auto-Layout" button to automatically arrange them
using WebCola's force-directed graph layout algorithm.

Run with:
    python examples/auto_layout_demo.py

Then in the browser:
- Click the "🔄 Auto-Layout" button to automatically arrange objects
- WebCola will:
  - Avoid overlaps between objects
  - Maintain reasonable connection lengths
  - Handle disconnected components
  - Create a visually pleasing layout
"""

from pathlib import Path
from py2max import Patcher
import random


def create_complex_patch():
    """Create a complex patch with many connections for auto-layout demo."""
    Path('outputs').mkdir(exist_ok=True)

    p = Patcher('outputs/auto_layout_demo.maxpat', title='Auto-Layout Demo')

    # Create a complex synthesizer
    # We'll randomize positions after creation

    # Control section
    metro = p.add_textbox('metro 250')
    toggle = p.add_message('1')

    # Oscillators
    osc1 = p.add_textbox('cycle~ 440')
    osc2 = p.add_textbox('saw~ 220')
    osc3 = p.add_textbox('tri~ 330')

    # Mixer
    mix = p.add_textbox('+~')

    # Filter
    filter_obj = p.add_textbox('lores~ 1000 0.5')

    # Envelope
    env = p.add_textbox('adsr~ 10 50 0.7 100')

    # VCA
    vca = p.add_textbox('*~')

    # Effects
    delay = p.add_textbox('delay~ 500')
    reverb = p.add_textbox('freeverb~')

    # Master gain
    master = p.add_textbox('gain~ 0.7')

    # Output
    dac = p.add_textbox('ezdac~')

    # Randomize all positions to create a messy layout
    # This will look chaotic until auto-layout is applied
    for box in p._boxes:
        box.patching_rect = [
            random.randint(50, 700),  # x
            random.randint(50, 500),  # y
            box.patching_rect[2],      # width
            box.patching_rect[3]       # height
        ]

    # Create connections (signal flow)
    # Control
    p.add_line(toggle, metro)
    p.add_line(metro, osc1)
    p.add_line(metro, osc2)
    p.add_line(metro, osc3)
    p.add_line(metro, env)

    # Audio mixing
    p.add_line(osc1, mix)
    p.add_line(osc2, mix)
    p.add_line(osc3, mix)

    # Filter and envelope
    p.add_line(mix, filter_obj)
    p.add_line(env, vca)
    p.add_line(filter_obj, vca)

    # Effects chain
    p.add_line(vca, delay)
    p.add_line(delay, reverb)
    p.add_line(reverb, master)

    # Output
    p.add_line(master, dac)
    p.add_line(master, dac, inlet=1)

    p.save()

    print(f"✅ Created auto-layout demo patch: {p._path}")
    print(f"\n📊 Patch statistics:")
    print(f"   Objects: {len(p._boxes)}")
    print(f"   Connections: {len(p._lines)}")
    print(f"\n🎯 Usage:")
    print(f"   1. Start the interactive server:")
    print(f"      py2max serve {p._path}")
    print(f"\n   2. In the browser:")
    print(f"      - Notice the randomly positioned objects (messy!)")
    print(f"      - Click the '🔄 Auto-Layout' button")
    print(f"      - Watch WebCola automatically arrange everything")
    print(f"\n   3. WebCola features:")
    print(f"      - Avoids overlapping objects")
    print(f"      - Maintains reasonable connection lengths")
    print(f"      - Handles multiple disconnected components")
    print(f"      - Creates visually pleasing layouts")


def create_hierarchical_patch():
    """Create a patch with hierarchical structure for auto-layout."""
    Path('outputs').mkdir(exist_ok=True)

    p = Patcher('outputs/auto_layout_hierarchical.maxpat', title='Hierarchical Layout Demo')

    # Create a hierarchical structure: source -> processors -> output

    # Sources
    sources = []
    for i in range(4):
        src = p.add_textbox(f'cycle~ {440 + i * 110}')
        sources.append(src)

    # First level processors
    proc1 = []
    for i in range(4):
        proc = p.add_textbox(f'*~ 0.{5 + i}')
        proc1.append(proc)

    # Second level processors
    proc2 = []
    for i in range(2):
        proc = p.add_textbox(f'+~')
        proc2.append(proc)

    # Final mix
    mix = p.add_textbox('+~')

    # Output
    dac = p.add_textbox('ezdac~')

    # Randomize all positions
    for box in p._boxes:
        box.patching_rect = [
            random.randint(50, 700),  # x
            random.randint(50, 500),  # y
            box.patching_rect[2],      # width
            box.patching_rect[3]       # height
        ]

    # Connect hierarchically
    for i, src in enumerate(sources):
        p.add_line(src, proc1[i])

    p.add_line(proc1[0], proc2[0])
    p.add_line(proc1[1], proc2[0])
    p.add_line(proc1[2], proc2[1])
    p.add_line(proc1[3], proc2[1])

    p.add_line(proc2[0], mix)
    p.add_line(proc2[1], mix)

    p.add_line(mix, dac)
    p.add_line(mix, dac, inlet=1)

    p.save()

    print(f"\n✅ Created hierarchical layout demo: {p._path}")
    print(f"   Objects: {len(p._boxes)}")
    print(f"   This demonstrates WebCola's ability to create hierarchical layouts")


def main():
    """Create all auto-layout demo patches."""
    print("=" * 70)
    print("Auto-Layout Demo - WebCola Force-Directed Graph Layout")
    print("=" * 70)
    print("\nCreating demo patches with random object positions...")

    create_complex_patch()
    create_hierarchical_patch()

    print("\n" + "=" * 70)
    print("Try it out!")
    print("=" * 70)
    print("\nThe patches have intentionally messy layouts.")
    print("Use the Auto-Layout button to see WebCola organize them!")
    print("=" * 70)


if __name__ == '__main__':
    main()
