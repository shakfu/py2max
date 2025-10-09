"""Demonstration of semantic object IDs feature.

This script shows how semantic IDs make patches more readable and debuggable
by using object-type-based IDs instead of generic numeric IDs.
"""

from pathlib import Path
from py2max import Patcher


def demo_numeric_ids():
    """Traditional numeric IDs (default behavior)."""
    print("\n=== Traditional Numeric IDs ===")
    p = Patcher('outputs/demo_numeric_ids.maxpat')

    osc1 = p.add_textbox('cycle~ 440')
    osc2 = p.add_textbox('cycle~ 220')
    gain = p.add_textbox('gain~')
    dac = p.add_textbox('ezdac~')

    p.add_line(osc1, gain)
    p.add_line(osc2, gain)
    p.add_line(gain, dac)

    print(f"Oscillator 1 ID: {osc1.id}")  # obj-1
    print(f"Oscillator 2 ID: {osc2.id}")  # obj-2
    print(f"Gain ID: {gain.id}")          # obj-3
    print(f"DAC ID: {dac.id}")            # obj-4

    p.save()
    print(f"Saved: {p._path}")


def demo_semantic_ids():
    """Semantic IDs based on object types."""
    print("\n=== Semantic Object IDs ===")
    p = Patcher('outputs/demo_semantic_ids.maxpat', semantic_ids=True)

    osc1 = p.add_textbox('cycle~ 440')
    osc2 = p.add_textbox('cycle~ 220')
    gain = p.add_textbox('gain~')
    dac = p.add_textbox('ezdac~')

    p.add_line(osc1, gain)
    p.add_line(osc2, gain)
    p.add_line(gain, dac)

    print(f"Oscillator 1 ID: {osc1.id}")  # cycle_1
    print(f"Oscillator 2 ID: {osc2.id}")  # cycle_2
    print(f"Gain ID: {gain.id}")          # gain_1
    print(f"DAC ID: {dac.id}")            # ezdac_1

    # Demonstrate object lookup by semantic ID
    found_osc1 = p.find_by_id('cycle_1')
    found_gain = p.find_by_id('gain_1')

    print(f"\nFound by ID 'cycle_1': {found_osc1.text}")
    print(f"Found by ID 'gain_1': {found_gain.text}")

    p.save()
    print(f"Saved: {p._path}")


def demo_complex_patch():
    """More complex patch showing semantic IDs with different object types."""
    print("\n=== Complex Patch with Semantic IDs ===")
    p = Patcher('outputs/demo_semantic_complex.maxpat', semantic_ids=True)

    # Control objects
    metro = p.add_textbox('metro 500')
    msg_start = p.add_message('start')
    msg_stop = p.add_message('stop')

    # Generators
    osc1 = p.add_textbox('cycle~ 440')
    osc2 = p.add_textbox('saw~ 220')
    noise = p.add_textbox('noise~')

    # Processors
    filter1 = p.add_textbox('lores~ 1000')
    gain1 = p.add_textbox('gain~ 0.5')
    gain2 = p.add_textbox('gain~ 0.3')

    # Output
    dac = p.add_textbox('ezdac~')

    # UI elements
    float1 = p.add_floatbox()
    float2 = p.add_floatbox()
    comment = p.add_comment('Two-oscillator synth with noise')

    # Connections
    p.add_line(metro, osc1)
    p.add_line(metro, osc2)
    p.add_line(osc1, filter1)
    p.add_line(osc2, gain1)
    p.add_line(noise, gain2)
    p.add_line(filter1, dac)
    p.add_line(gain1, dac, inlet=1)
    p.add_line(gain2, dac)

    print("\nObject IDs in complex patch:")
    print(f"Metro: {metro.id}")           # metro_1
    print(f"Start message: {msg_start.id}")  # message_1
    print(f"Stop message: {msg_stop.id}")    # message_2
    print(f"Cycle~: {osc1.id}")          # cycle_1
    print(f"Saw~: {osc2.id}")            # saw_1
    print(f"Noise~: {noise.id}")         # noise_1
    print(f"Filter: {filter1.id}")       # lores_1
    print(f"Gain 1: {gain1.id}")         # gain_1
    print(f"Gain 2: {gain2.id}")         # gain_2
    print(f"DAC: {dac.id}")              # ezdac_1
    print(f"Float 1: {float1.id}")       # flonum_1
    print(f"Float 2: {float2.id}")       # flonum_2
    print(f"Comment: {comment.id}")      # comment_1

    # Search by object type
    gains = p.find_by_text('gain~')
    print(f"\nFound {len(gains)} gain~ objects")

    p.save()
    print(f"Saved: {p._path}")


def demo_sanitization():
    """Show how object names are sanitized for IDs."""
    print("\n=== ID Sanitization Examples ===")
    p = Patcher('outputs/demo_sanitization.maxpat', semantic_ids=True)

    # Special characters removed
    obj1 = p.add_textbox('cycle~ 440')      # ~ removed
    obj2 = p.add_textbox('delay~ 500')      # ~ removed
    obj3 = p.add_textbox('test.obj 123')    # . removed
    obj4 = p.add_textbox('test-obj')        # - removed
    obj5 = p.add_textbox('test[obj]')       # [] removed
    obj6 = p.add_textbox('test(obj)')       # () removed

    print(f"'cycle~ 440' → ID: {obj1.id}")      # cycle_1
    print(f"'delay~ 500' → ID: {obj2.id}")      # delay_1
    print(f"'test.obj 123' → ID: {obj3.id}")    # testobj_1
    print(f"'test-obj' → ID: {obj4.id}")        # testobj_2
    print(f"'test[obj]' → ID: {obj5.id}")       # testobj_3
    print(f"'test(obj)' → ID: {obj6.id}")       # testobj_4

    p.save()
    print(f"Saved: {p._path}")


def main():
    """Run all semantic IDs demonstrations."""
    # Create outputs directory if it doesn't exist
    Path('outputs').mkdir(exist_ok=True)

    print("=" * 60)
    print("Semantic Object IDs Demonstration")
    print("=" * 60)

    demo_numeric_ids()
    demo_semantic_ids()
    demo_complex_patch()
    demo_sanitization()

    print("\n" + "=" * 60)
    print("All demos completed. Check the outputs/ directory.")
    print("=" * 60)


if __name__ == '__main__':
    main()
