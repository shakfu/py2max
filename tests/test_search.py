"""Tests for object search methods."""

from py2max import Patcher


def test_find_by_id():
    """Test finding boxes by ID."""
    p = Patcher('test.maxpat')
    osc = p.add_textbox('cycle~ 440')
    gain = p.add_textbox('gain~')
    dac = p.add_textbox('ezdac~')

    # Find by ID
    found = p.find_by_id(osc.id)
    assert found is osc
    assert found.text == 'cycle~ 440'

    found_gain = p.find_by_id(gain.id)
    assert found_gain is gain

    # Non-existent ID
    not_found = p.find_by_id('obj-9999')
    assert not_found is None


def test_find_by_type():
    """Test finding boxes by Max object type."""
    p = Patcher('test.maxpat')
    osc = p.add_textbox('cycle~ 440')
    gain = p.add_textbox('gain~')
    msg = p.add_message('bang')
    comment = p.add_comment('This is a comment')

    # Some objects may have specific maxclass from defaults, others are 'newobj'
    # Just check that we can find them
    all_boxes = p._boxes
    assert len(all_boxes) == 4

    # Find messages
    messages = p.find_by_type('message')
    assert len(messages) == 1
    assert msg in messages

    # Find comments
    comments = p.find_by_type('comment')
    assert len(comments) == 1
    assert comment in comments

    # Non-existent type
    panels = p.find_by_type('panel')
    assert len(panels) == 0


def test_find_by_text():
    """Test finding boxes by text content."""
    p = Patcher('test.maxpat')
    osc1 = p.add_textbox('cycle~ 440')
    osc2 = p.add_textbox('saw~ 220')
    osc3 = p.add_textbox('Cycle~ 880')  # Different case
    gain = p.add_textbox('gain~ 0.5')
    dac = p.add_textbox('ezdac~')

    # Find all MSP objects (contain ~)
    msp_objects = p.find_by_text('~')
    assert len(msp_objects) == 5

    # Find oscillators (case insensitive by default)
    oscillators = p.find_by_text('cycle')
    assert len(oscillators) == 2
    assert osc1 in oscillators
    assert osc3 in oscillators

    # Case sensitive search
    exact_cycle = p.find_by_text('cycle', case_sensitive=True)
    assert len(exact_cycle) == 1
    assert osc1 in exact_cycle
    assert osc3 not in exact_cycle

    # Find by partial match
    gain_objects = p.find_by_text('gain')
    assert len(gain_objects) == 1
    assert gain in gain_objects

    # Find by number
    freq_440 = p.find_by_text('440')
    assert len(freq_440) == 1
    assert osc1 in freq_440

    # Non-existent text
    not_found = p.find_by_text('nonexistent')
    assert len(not_found) == 0


def test_search_complex_patch():
    """Test search methods on a more complex patch."""
    p = Patcher('complex.maxpat')

    # Build a simple synth
    metro = p.add_textbox('metro 500')
    osc1 = p.add_textbox('cycle~ 440')
    osc2 = p.add_textbox('saw~ 220')
    filter1 = p.add_textbox('lores~ 1000')
    gain = p.add_textbox('gain~ 0.5')
    dac = p.add_textbox('ezdac~')

    # Add some messages and comments
    msg1 = p.add_message('start')
    msg2 = p.add_message('stop')
    comment = p.add_comment('Simple synth patch')

    # Find all oscillators
    oscillators = [b for b in p.find_by_text('~') if 'cycle' in b.text.lower() or 'saw' in b.text.lower()]
    assert len(oscillators) == 2

    # Find all filters
    filters = p.find_by_text('lores')
    assert len(filters) == 1

    # Find control objects (non-MSP)
    non_msp = [b for b in p.find_by_type('newobj') if '~' not in getattr(b, 'text', '')]
    assert metro in non_msp

    # Find all messages
    messages = p.find_by_type('message')
    assert len(messages) == 2
    assert msg1 in messages
    assert msg2 in messages


def test_search_empty_patch():
    """Test search methods on an empty patch."""
    p = Patcher('empty.maxpat')

    # All searches should return empty
    assert p.find_by_id('obj-1') is None
    assert len(p.find_by_type('newobj')) == 0
    assert len(p.find_by_text('anything')) == 0


def test_search_chaining():
    """Test chaining multiple search criteria."""
    p = Patcher('chain.maxpat')

    # Create variety of objects
    p.add_textbox('cycle~ 440')
    p.add_textbox('cycle~ 880')
    p.add_textbox('saw~ 220')
    p.add_textbox('gain~ 0.5')
    msg = p.add_message('440')
    comment = p.add_comment('cycle~ info')

    # Total should be 6 boxes
    assert len(p._boxes) == 6

    # Filter all boxes by text containing 'cycle'
    cycles = p.find_by_text('cycle')
    assert len(cycles) == 3  # 2 cycle~ objects + 1 comment

    # Messages and comments with same text should be findable
    all_440 = p.find_by_text('440')
    assert len(all_440) >= 2  # At least cycle~ 440 object + message
    assert msg in all_440
