"""Demonstration of SVG preview functionality.

This example shows how to use py2max's SVG export feature to create
visual previews of Max patches without needing Max installed.

Features demonstrated:
- Basic SVG export
- Using the preview CLI command
- Different layout strategies
- Customizing SVG output
"""

from pathlib import Path
import tempfile
from py2max import Patcher, export_svg


def demo_basic_preview():
    """Basic SVG preview example."""
    print("Creating basic synth patch with SVG preview...")

    p = Patcher('basic_synth.maxpat', layout='grid')
    metro = p.add_textbox('metro 500')
    osc = p.add_textbox('cycle~ 440')
    gain = p.add_textbox('gain~ 0.5')
    dac = p.add_textbox('ezdac~')

    p.add_line(metro, osc)
    p.add_line(osc, gain)
    p.add_line(gain, dac)
    p.add_line(gain, dac, inlet=1)

    # Save maxpat
    p.save()

    # Export to SVG for preview
    svg_path = Path('basic_synth.svg')
    export_svg(p, svg_path, title="Basic Synth Patch")
    print(f"  Saved SVG preview to: {svg_path}")
    print(f"  Open in browser: file://{svg_path.absolute()}")


def demo_complex_preview():
    """Complex patch with multiple signal paths."""
    print("\nCreating complex multi-voice patch with SVG preview...")

    p = Patcher('complex_synth.maxpat', layout='flow', flow_direction='vertical')

    # Control section
    metro = p.add_textbox('metro 250')
    button = p.add_textbox('button')

    # Voice 1
    osc1 = p.add_textbox('cycle~ 440')
    filter1 = p.add_textbox('lores~ 1000')

    # Voice 2
    osc2 = p.add_textbox('saw~ 220')
    filter2 = p.add_textbox('lores~ 500')

    # Mix and output
    mix = p.add_textbox('+~')
    gain = p.add_textbox('gain~ 0.5')
    reverb = p.add_textbox('reverb~')
    dac = p.add_textbox('ezdac~')

    # Connections
    p.add_line(metro, osc1)
    p.add_line(metro, osc2)
    p.add_line(button, metro)
    p.add_line(osc1, filter1)
    p.add_line(osc2, filter2)
    p.add_line(filter1, mix)
    p.add_line(filter2, mix, inlet=1)
    p.add_line(mix, gain)
    p.add_line(gain, reverb)
    p.add_line(reverb, dac)
    p.add_line(reverb, dac, inlet=1)

    p.optimize_layout()
    p.save()

    # Export to SVG
    svg_path = Path('complex_synth.svg')
    export_svg(p, svg_path, title="Complex Multi-Voice Synth", show_ports=True)
    print(f"  Saved SVG preview to: {svg_path}")


def demo_layout_comparison():
    """Compare different layout strategies via SVG."""
    print("\nComparing different layout strategies...")

    layouts = ['horizontal', 'vertical', 'grid', 'flow']

    for layout_type in layouts:
        p = Patcher(f'{layout_type}_layout.maxpat', layout=layout_type)

        metro = p.add_textbox('metro 500')
        osc = p.add_textbox('cycle~ 440')
        filter = p.add_textbox('lores~ 1000')
        gain = p.add_textbox('gain~ 0.5')
        dac = p.add_textbox('ezdac~')

        p.add_line(metro, osc)
        p.add_line(osc, filter)
        p.add_line(filter, gain)
        p.add_line(gain, dac)

        if layout_type in ['grid', 'flow']:
            p.optimize_layout()

        p.save()

        # Export to SVG
        svg_path = Path(f'{layout_type}_layout.svg')
        export_svg(p, svg_path, title=f"{layout_type.capitalize()} Layout")
        print(f"  {layout_type}: {svg_path}")


def demo_custom_styling():
    """Demonstrate SVG export with different options."""
    print("\nDemonstrating custom SVG options...")

    p = Patcher('styled_patch.maxpat')
    comment = p.add_comment('This is a comment - should be yellow')
    msg = p.add_message('bang')
    osc = p.add_textbox('cycle~ 440')

    p.save()

    # Export with ports
    svg_with_ports = Path('styled_with_ports.svg')
    export_svg(p, svg_with_ports, show_ports=True, title="With Inlet/Outlet Ports")
    print(f"  With ports: {svg_with_ports}")

    # Export without ports
    svg_no_ports = Path('styled_no_ports.svg')
    export_svg(p, svg_no_ports, show_ports=False, title="Without Ports")
    print(f"  Without ports: {svg_no_ports}")

    # Export without title
    svg_no_title = Path('styled_no_title.svg')
    export_svg(p, svg_no_title, show_ports=True, title=None)
    print(f"  Without title: {svg_no_title}")


def demo_cli_usage():
    """Demonstrate CLI preview command usage."""
    print("\nCLI Usage Examples:")
    print("=" * 60)
    print()
    print("1. Basic preview (saves to /tmp):")
    print("   py2max preview my-patch.maxpat")
    print()
    print("2. Preview with custom output path:")
    print("   py2max preview my-patch.maxpat -o output.svg")
    print()
    print("3. Preview with custom title:")
    print("   py2max preview my-patch.maxpat --title 'My Synth'")
    print()
    print("4. Preview without ports:")
    print("   py2max preview my-patch.maxpat --no-ports")
    print()
    print("5. Preview and open in browser:")
    print("   py2max preview my-patch.maxpat --open")
    print()
    print("6. Preview without title:")
    print("   py2max preview my-patch.maxpat --no-title")
    print()
    print("7. Combine options:")
    print("   py2max preview my-patch.maxpat -o synth.svg --title 'Synth' --open")
    print()


def demo_programmatic_workflow():
    """Show complete workflow from creation to preview."""
    print("\nComplete Workflow: Create -> Save -> Preview")
    print("=" * 60)

    # Step 1: Create patch
    print("\n1. Creating patch...")
    p = Patcher('workflow_demo.maxpat', layout='grid')
    metro = p.add_textbox('metro 1000')
    random = p.add_textbox('random 127')
    mtof = p.add_textbox('mtof')
    osc = p.add_textbox('cycle~')
    gain = p.add_textbox('gain~ 0.3')
    dac = p.add_textbox('ezdac~')

    p.add_line(metro, random)
    p.add_line(random, mtof)
    p.add_line(mtof, osc)
    p.add_line(osc, gain)
    p.add_line(gain, dac)
    p.add_line(gain, dac, inlet=1)

    p.optimize_layout()

    # Step 2: Save maxpat
    print("2. Saving .maxpat file...")
    p.save()

    # Step 3: Generate SVG preview
    print("3. Generating SVG preview...")
    svg_path = Path('workflow_demo.svg')
    export_svg(p, svg_path, title="Random Note Generator")

    print(f"\nDone! Files created:")
    print(f"  Max patch: workflow_demo.maxpat")
    print(f"  SVG preview: {svg_path}")
    print(f"\nView SVG in browser:")
    print(f"  file://{svg_path.absolute()}")


def demo_temp_preview():
    """Show how to use temporary files for quick previews."""
    print("\nQuick preview using temporary file...")

    p = Patcher('temp_test.maxpat')
    osc1 = p.add_textbox('cycle~ 440')
    osc2 = p.add_textbox('saw~ 220')
    mix = p.add_textbox('+~')
    dac = p.add_textbox('ezdac~')

    p.add_line(osc1, mix)
    p.add_line(osc2, mix, inlet=1)
    p.add_line(mix, dac)

    # Use temporary directory
    temp_dir = Path(tempfile.gettempdir())
    svg_path = temp_dir / 'quick_preview.svg'

    export_svg(p, svg_path, title="Quick Preview")
    print(f"  Preview saved to: {svg_path}")
    print(f"  This file will be cleaned up by the OS")


if __name__ == '__main__':
    print("py2max SVG Preview Demonstration")
    print("=" * 60)

    demo_basic_preview()
    demo_complex_preview()
    demo_layout_comparison()
    demo_custom_styling()
    demo_temp_preview()
    demo_programmatic_workflow()
    demo_cli_usage()

    print("\n" + "=" * 60)
    print("All examples complete!")
    print("\nTo view any SVG file, open it in a web browser:")
    print("  - Double-click the .svg file")
    print("  - Or use: open <filename>.svg (macOS)")
    print("  - Or drag & drop into browser window")
