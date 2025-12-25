"""Demo of the improved info() command.

This script demonstrates the info() command with both normal and verbose modes.
"""

from pathlib import Path
from py2max import Patcher


def demo_info_command():
    """Demonstrate the info() command."""
    # Create a test patch
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    patch_path = output_dir / "info_demo.maxpat"

    print("Creating demo patch with multiple objects and connections...")
    print()

    # Create patcher with some objects
    p = Patcher(patch_path, layout="flow")

    # Create a simple synth patch
    metro = p.add("metro 500", id="metro-1")
    random_obj = p.add("random 127", id="random-1")
    osc = p.add("cycle~ 440", id="osc-1")
    gain = p.add("gain~ 0.5", id="gain-1")
    dac = p.add("ezdac~", id="dac-1")

    # Connect them
    p.link(metro, random_obj)
    p.link(random_obj, osc)
    p.link(osc, gain)
    p.link(gain, dac, inlet=0)
    p.link(gain, dac, inlet=1)

    p.optimize_layout()
    p.save()

    print("✓ Created patch with 5 objects and 5 connections")
    print()

    # Simulate what the REPL would show
    print("=" * 70)
    print("DEMO: info() command (normal mode)")
    print("=" * 70)
    print()
    print("In REPL, you would type: info()")
    print()
    print("Output:")
    print()

    # Mock the server for demo
    class MockHandler:
        clients = []

    class MockServer:
        port = 8000
        handler = MockHandler()

    # Create commands object
    from py2max.repl import ReplCommands

    commands = ReplCommands(p, MockServer())

    # Show normal info
    commands.info()

    print()
    print("=" * 70)
    print("DEMO: info(verbose=True) command (detailed mode)")
    print("=" * 70)
    print()
    print("In REPL, you would type: info(True)")
    print()
    print("Output:")
    print()

    # Show verbose info
    commands.info(verbose=True)

    print()
    print("=" * 70)
    print("KEY IMPROVEMENTS:")
    print("=" * 70)
    print()
    print("1. info() shows quick summary (same as before)")
    print("2. info(True) shows:")
    print("   - Complete list of all boxes with IDs, types, and positions")
    print("   - Complete list of all connections showing:")
    print("     * Source box ID and name")
    print("     * Outlet number")
    print("     * Destination box ID and name")
    print("     * Inlet number")
    print()
    print("3. Easy to see:")
    print("   - Which boxes are connected to which")
    print("   - What outlets/inlets are being used")
    print("   - The full signal flow through the patch")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    demo_info_command()
