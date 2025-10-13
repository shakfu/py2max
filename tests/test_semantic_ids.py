"""Tests for semantic object IDs feature."""

from pathlib import Path
import tempfile
from py2max import Patcher


def test_semantic_ids_disabled_by_default():
    """Test that semantic IDs are disabled by default."""
    p = Patcher("test.maxpat")
    osc = p.add_textbox("cycle~ 440")
    assert osc.id == "obj-1"

    gain = p.add_textbox("gain~")
    assert gain.id == "obj-2"


def test_semantic_ids_enabled():
    """Test that semantic IDs work when enabled."""
    p = Patcher("test.maxpat", semantic_ids=True)
    osc = p.add_textbox("cycle~ 440")
    assert osc.id == "cycle_1"

    gain = p.add_textbox("gain~")
    assert gain.id == "gain_1"

    # Second instance of same object type
    osc2 = p.add_textbox("cycle~ 220")
    assert osc2.id == "cycle_2"


def test_semantic_ids_sanitization():
    """Test that special characters are sanitized in semantic IDs."""
    p = Patcher("test.maxpat", semantic_ids=True)

    # Tilde removed
    osc = p.add_textbox("cycle~ 440")
    assert osc.id == "cycle_1"

    # Spaces replaced with underscores
    metro = p.add_textbox("metro 500")
    assert "metro" in metro.id

    # Dots, dashes, brackets, parens removed
    p2 = Patcher("test2.maxpat", semantic_ids=True)
    obj1 = p2.add_textbox("test.obj")
    obj2 = p2.add_textbox("test-obj")
    obj3 = p2.add_textbox("test[obj]")
    obj4 = p2.add_textbox("test(obj)")

    assert "." not in obj1.id
    assert "-" not in obj2.id
    assert "[" not in obj3.id and "]" not in obj3.id
    assert "(" not in obj4.id and ")" not in obj4.id


def test_semantic_ids_counter_increment():
    """Test that counters increment correctly for same object types."""
    p = Patcher("test.maxpat", semantic_ids=True)

    osc1 = p.add_textbox("cycle~ 440")
    osc2 = p.add_textbox("cycle~ 220")
    osc3 = p.add_textbox("cycle~ 110")

    assert osc1.id == "cycle_1"
    assert osc2.id == "cycle_2"
    assert osc3.id == "cycle_3"

    # Different object type starts its own counter
    gain1 = p.add_textbox("gain~")
    gain2 = p.add_textbox("gain~")

    assert gain1.id == "gain_1"
    assert gain2.id == "gain_2"


def test_semantic_ids_with_message():
    """Test semantic IDs with message objects."""
    p = Patcher("test.maxpat", semantic_ids=True)

    msg1 = p.add_message("hello")
    msg2 = p.add_message("world")

    assert msg1.id == "message_1"
    assert msg2.id == "message_2"


def test_semantic_ids_with_comment():
    """Test semantic IDs with comment objects."""
    p = Patcher("test.maxpat", semantic_ids=True)

    cmt1 = p.add_comment("comment 1")
    cmt2 = p.add_comment("comment 2")

    assert cmt1.id == "comment_1"
    assert cmt2.id == "comment_2"


def test_semantic_ids_with_number_boxes():
    """Test semantic IDs with number boxes."""
    p = Patcher("test.maxpat", semantic_ids=True)

    int1 = p.add_intbox()
    int2 = p.add_intbox()

    assert int1.id == "number_1"
    assert int2.id == "number_2"

    float1 = p.add_floatbox()
    float2 = p.add_floatbox()

    assert float1.id == "flonum_1"
    assert float2.id == "flonum_2"


def test_semantic_ids_with_containers():
    """Test semantic IDs with container objects."""
    p = Patcher("test.maxpat", semantic_ids=True)

    coll1 = p.add_coll("data1")
    coll2 = p.add_coll("data2")

    assert coll1.id == "coll_1"
    assert coll2.id == "coll_2"

    dict1 = p.add_dict("dict1")
    dict2 = p.add_dict("dict2")

    assert dict1.id == "dict_1"
    assert dict2.id == "dict_2"

    table1 = p.add_table("table1")
    table2 = p.add_table("table2")

    assert table1.id == "table_1"
    assert table2.id == "table_2"


def test_semantic_ids_with_codebox():
    """Test semantic IDs with codebox objects."""
    p = Patcher("test.maxpat", semantic_ids=True)

    code1 = p.add_codebox("out1 = in1 * 2;")
    code2 = p.add_codebox("out1 = in1 + 1;")

    assert code1.id == "codebox_1"
    assert code2.id == "codebox_2"

    # codebox~ sanitizes to same name as codebox, so shares counter
    code_tilde = p.add_codebox_tilde("out1 = in1 * 0.5;")
    assert code_tilde.id == "codebox_3"


def test_semantic_ids_with_subpatchers():
    """Test semantic IDs with subpatcher objects."""
    p = Patcher("test.maxpat", semantic_ids=True)

    sub1 = p.add_subpatcher("p subpatch1")
    sub2 = p.add_subpatcher("p subpatch2")

    assert sub1.id == "p_1"
    assert sub2.id == "p_2"


def test_semantic_ids_with_umenu():
    """Test semantic IDs with umenu objects."""
    p = Patcher("test.maxpat", semantic_ids=True)

    menu1 = p.add_umenu(items=["option1", "option2"])
    menu2 = p.add_umenu(items=["choice1", "choice2"])

    assert menu1.id == "umenu_1"
    assert menu2.id == "umenu_2"


def test_semantic_ids_with_bpatcher():
    """Test semantic IDs with bpatcher objects."""
    p = Patcher("test.maxpat", semantic_ids=True)

    bp1 = p.add_bpatcher("my-patch.maxpat")
    bp2 = p.add_bpatcher("another-patch.maxpat")

    assert bp1.id == "bpatcher_1"
    assert bp2.id == "bpatcher_2"


def test_semantic_ids_with_custom_id():
    """Test that custom IDs override semantic IDs."""
    p = Patcher("test.maxpat", semantic_ids=True)

    osc = p.add_textbox("cycle~ 440", id="my-custom-id")
    assert osc.id == "my-custom-id"

    # Next cycle should still be cycle_1 (counter not incremented)
    osc2 = p.add_textbox("cycle~ 220")
    assert osc2.id == "cycle_1"


def test_semantic_ids_persistence():
    """Test that semantic IDs persist when saving and loading."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "semantic_test.maxpat"

        # Create patch with semantic IDs
        p1 = Patcher(path, semantic_ids=True)
        osc = p1.add_textbox("cycle~ 440")
        gain = p1.add_textbox("gain~")
        p1.save()

        assert osc.id == "cycle_1"
        assert gain.id == "gain_1"

        # Load patch and verify IDs are preserved
        p2 = Patcher.from_file(path)
        boxes = p2._boxes

        assert len(boxes) == 2
        assert boxes[0].id == "cycle_1"
        assert boxes[1].id == "gain_1"


def test_semantic_ids_mixed_objects():
    """Test semantic IDs with a mix of different object types."""
    p = Patcher("test.maxpat", semantic_ids=True)

    # Create a typical synth patch
    metro = p.add_textbox("metro 500")
    cycle1 = p.add_textbox("cycle~ 440")
    cycle2 = p.add_textbox("cycle~ 220")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")
    msg = p.add_message("start")
    comment = p.add_comment("Simple oscillator")

    # Verify all have semantic IDs
    assert "metro" in metro.id
    assert cycle1.id == "cycle_1"
    assert cycle2.id == "cycle_2"
    assert gain.id == "gain_1"
    assert "ezdac" in dac.id
    assert msg.id == "message_1"
    assert comment.id == "comment_1"


def test_semantic_ids_backwards_compatibility():
    """Test that non-semantic mode is unchanged (backward compatibility)."""
    p = Patcher("test.maxpat")  # semantic_ids=False by default

    osc1 = p.add_textbox("cycle~ 440")
    osc2 = p.add_textbox("cycle~ 220")
    gain = p.add_textbox("gain~")
    msg = p.add_message("test")

    # Should use traditional obj-N naming
    assert osc1.id == "obj-1"
    assert osc2.id == "obj-2"
    assert gain.id == "obj-3"
    assert msg.id == "obj-4"
