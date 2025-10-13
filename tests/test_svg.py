"""Tests for SVG export functionality."""

import tempfile
from pathlib import Path

import pytest

from py2max import Patcher, export_svg, export_svg_string


def test_svg_export_basic():
    """Test basic SVG export with simple patch."""
    p = Patcher("test.maxpat")
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")
    p.add_line(osc, gain)
    p.add_line(gain, dac)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.svg"
        export_svg(p, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert '<?xml version="1.0" encoding="UTF-8"?>' in content
        assert '<svg xmlns="http://www.w3.org/2000/svg"' in content
        assert "</svg>" in content
        assert "cycle~ 440" in content
        assert "gain~" in content
        assert "ezdac~" in content


def test_svg_export_with_title():
    """Test SVG export with custom title."""
    p = Patcher("test.maxpat")
    osc = p.add_textbox("cycle~ 440")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.svg"
        export_svg(p, output_path, title="Test Patch")

        content = output_path.read_text()
        assert "Test Patch" in content


def test_svg_export_without_ports():
    """Test SVG export with ports disabled."""
    p = Patcher("test.maxpat")
    osc = p.add_textbox("cycle~ 440")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.svg"
        export_svg(p, output_path, show_ports=False)

        content = output_path.read_text()
        # Should not contain port circles
        assert content.count("<circle") == 0


def test_svg_export_with_ports():
    """Test SVG export with ports enabled."""
    p = Patcher("test.maxpat")
    osc = p.add_textbox("cycle~ 440")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.svg"
        export_svg(p, output_path, show_ports=True)

        content = output_path.read_text()
        # Should contain port circles
        assert "<circle" in content


def test_svg_export_string():
    """Test SVG export to string."""
    p = Patcher("test.maxpat")
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    p.add_line(osc, gain)

    svg_content = export_svg_string(p)

    assert isinstance(svg_content, str)
    assert '<?xml version="1.0" encoding="UTF-8"?>' in svg_content
    assert '<svg xmlns="http://www.w3.org/2000/svg"' in svg_content
    assert "</svg>" in svg_content
    assert "cycle~ 440" in svg_content
    assert "gain~" in svg_content


def test_svg_export_empty_patch():
    """Test SVG export with empty patch."""
    p = Patcher("test.maxpat")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.svg"
        export_svg(p, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "<svg" in content
        assert "</svg>" in content


def test_svg_export_comments():
    """Test SVG export with comment boxes."""
    p = Patcher("test.maxpat")
    comment = p.add_comment("This is a comment")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.svg"
        export_svg(p, output_path)

        content = output_path.read_text()
        assert "This is a comment" in content
        # Comments should have yellow fill
        assert "#ffffd0" in content


def test_svg_export_messages():
    """Test SVG export with message boxes."""
    p = Patcher("test.maxpat")
    msg = p.add_message("bang")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.svg"
        export_svg(p, output_path)

        content = output_path.read_text()
        assert "bang" in content


def test_svg_export_patchlines():
    """Test SVG export with patchlines."""
    p = Patcher("test.maxpat")
    osc1 = p.add_textbox("cycle~ 440")
    osc2 = p.add_textbox("saw~ 220")
    mix = p.add_textbox("+~")
    p.add_line(osc1, mix)
    p.add_line(osc2, mix, inlet=1)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.svg"
        export_svg(p, output_path)

        content = output_path.read_text()
        # Should contain line elements
        assert "<line" in content
        # Should have multiple lines
        assert content.count("<line") >= 2


def test_svg_export_complex_patch():
    """Test SVG export with complex patch layout."""
    p = Patcher("test.maxpat", layout="grid")
    metro = p.add_textbox("metro 500")
    osc1 = p.add_textbox("cycle~ 440")
    osc2 = p.add_textbox("saw~ 220")
    filter = p.add_textbox("lores~ 1000")
    gain = p.add_textbox("gain~ 0.5")
    dac = p.add_textbox("ezdac~")

    p.add_line(metro, osc1)
    p.add_line(metro, osc2)
    p.add_line(osc1, filter)
    p.add_line(osc2, gain)
    p.add_line(filter, gain)
    p.add_line(gain, dac)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.svg"
        export_svg(p, output_path, title="Complex Synth Patch")

        assert output_path.exists()
        content = output_path.read_text()
        assert "Complex Synth Patch" in content
        assert "metro 500" in content
        assert "cycle~ 440" in content
        assert "saw~ 220" in content
        assert "lores~ 1000" in content
        assert "gain~ 0.5" in content
        assert "ezdac~" in content
        # Should have multiple patchlines
        assert content.count("<line") >= 6


def test_svg_export_different_layouts():
    """Test SVG export with different layout managers."""
    for layout in ["horizontal", "vertical", "grid", "flow"]:
        p = Patcher("test.maxpat", layout=layout)
        osc = p.add_textbox("cycle~ 440")
        gain = p.add_textbox("gain~")
        dac = p.add_textbox("ezdac~")
        p.add_line(osc, gain)
        p.add_line(gain, dac)
        p.optimize_layout()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / f"test_{layout}.svg"
            export_svg(p, output_path)

            assert output_path.exists()
            content = output_path.read_text()
            assert "cycle~ 440" in content
            assert "gain~" in content
            assert "ezdac~" in content


def test_svg_text_escaping():
    """Test that special characters in text are properly escaped."""
    p = Patcher("test.maxpat")
    # Add box with special characters
    box = p.add_textbox('print <test> & "value"')

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.svg"
        export_svg(p, output_path)

        content = output_path.read_text()
        # Should be escaped in SVG
        assert "&lt;test&gt;" in content or "test" in content
        assert "&amp;" in content or "&" in content


def test_svg_viewbox_calculation():
    """Test that viewBox is calculated correctly."""
    p = Patcher("test.maxpat")
    osc = p.add_textbox("cycle~ 440")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.svg"
        export_svg(p, output_path)

        content = output_path.read_text()
        # Should have viewBox attribute
        assert "viewBox=" in content
        # Should have width and height
        assert "width=" in content
        assert "height=" in content


def test_svg_cli_command(tmp_path):
    """Test CLI preview command."""
    from py2max.cli import main

    # Create a test patch
    test_patch = tmp_path / "test.maxpat"
    p = Patcher(test_patch)
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    p.add_line(osc, gain)
    p.save()

    # Test preview command with output path
    output_svg = tmp_path / "test.svg"
    result = main(["preview", str(test_patch), "-o", str(output_svg)])

    assert result == 0
    assert output_svg.exists()
    content = output_svg.read_text()
    assert "cycle~ 440" in content
    assert "gain~" in content


def test_svg_cli_command_no_output(tmp_path):
    """Test CLI preview command without explicit output path."""
    from py2max.cli import main

    # Create a test patch
    test_patch = tmp_path / "test.maxpat"
    p = Patcher(test_patch)
    osc = p.add_textbox("cycle~ 440")
    p.save()

    # Test preview command without output (should use /tmp)
    result = main(["preview", str(test_patch)])

    assert result == 0
    # Check that SVG was created in /tmp
    import tempfile

    temp_dir = Path(tempfile.gettempdir())
    svg_path = temp_dir / "test_preview.svg"
    assert svg_path.exists()
    content = svg_path.read_text()
    assert "cycle~ 440" in content
    # Clean up
    svg_path.unlink()


def test_svg_cli_command_with_options(tmp_path):
    """Test CLI preview command with various options."""
    from py2max.cli import main

    # Create a test patch
    test_patch = tmp_path / "test.maxpat"
    p = Patcher(test_patch)
    osc = p.add_textbox("cycle~ 440")
    p.save()

    # Test with custom title and no ports
    output_svg = tmp_path / "test_options.svg"
    result = main(
        [
            "preview",
            str(test_patch),
            "-o",
            str(output_svg),
            "--title",
            "Custom Title",
            "--no-ports",
        ]
    )

    assert result == 0
    assert output_svg.exists()
    content = output_svg.read_text()
    assert "Custom Title" in content
    # Should not have circles (ports)
    assert content.count("<circle") == 0


def test_svg_cli_command_nonexistent_file(tmp_path):
    """Test CLI preview command with nonexistent file."""
    from py2max.cli import main

    nonexistent = tmp_path / "nonexistent.maxpat"
    result = main(["preview", str(nonexistent)])

    assert result == 1  # Should fail
