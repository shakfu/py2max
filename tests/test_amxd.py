"""Tests for .amxd (Max for Live) binary format read/write."""

import json
import struct
from pathlib import Path

import pytest

from py2max import Patcher
from py2max.m4l import (
    DEVICE_TYPES,
    ensure_amxd_project_block,
    pack_amxd,
    read_amxd,
    unpack_amxd,
    write_amxd,
)
from py2max.core.common import Rect
from py2max.exceptions import PatcherIOError


OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


def _build_patcher(path: str) -> Patcher:
    p = Patcher(path)
    osc = p.add_textbox("cycle~ 440")
    gain = p.add_textbox("gain~")
    dac = p.add_textbox("ezdac~")
    p.add_line(osc, gain)
    p.add_line(gain, dac)
    return p


def test_pack_header_layout():
    payload = b'{"hello": "world"}'
    data = pack_amxd(payload, patcher_filename="hello.maxpat", mtime=0x12345678)

    # Header (offsets 0-35) — see py2max/m4l.py docstring.
    assert data[0:4] == b"ampf"
    assert struct.unpack("<I", data[4:8])[0] == 4
    assert data[8:12] == b"aaaa"
    assert data[12:16] == b"ptch"
    # ptch payload size (LE) covers everything from offset 20 to end.
    assert struct.unpack("<I", data[16:20])[0] == len(data) - 20
    assert data[20:24] == b"mx@c"
    assert struct.unpack(">I", data[24:28])[0] == 16
    assert struct.unpack(">I", data[28:32])[0] == 0
    # mx@c content size = 16-byte preamble + JSON + NUL.
    assert struct.unpack(">I", data[32:36])[0] == 16 + len(payload) + 1
    # JSON starts at offset 36 and is NUL-terminated.
    assert data[36 : 36 + len(payload)] == payload
    assert data[36 + len(payload) : 36 + len(payload) + 1] == b"\x00"


def test_pack_byte_for_byte_matches_max_export():
    """Re-pack the JSON from a real Max-exported .amxd; bytes must match exactly."""
    fixtures = [
        ("outputs/mydevice.amxd", "mydevice.maxpat", 3859919929),
        ("outputs/mydevice2.amxd", "mydevice2.maxpat", 3859920850),
    ]
    for rel, fnam, mtime in fixtures:
        path = Path(rel)
        if not path.exists():
            pytest.skip(f"missing fixture: {rel}")
        original = path.read_bytes()
        json_bytes, dt = unpack_amxd(original)
        repacked = pack_amxd(
            json_bytes, device_type=dt, patcher_filename=fnam, mtime=mtime
        )
        assert repacked == original, f"mismatch for {rel}"


def test_pack_accepts_str_and_bytes():
    s = '{"a": 1}'
    assert pack_amxd(s) == pack_amxd(s.encode("utf-8"))


def test_roundtrip_bytes():
    original = '{"patcher": {"boxes": [], "lines": []}}'
    data = pack_amxd(original)
    payload, device_type = unpack_amxd(data)
    assert json.loads(payload) == json.loads(original)
    assert device_type == "audio_effect"


def test_unpack_rejects_short_data():
    with pytest.raises(PatcherIOError):
        unpack_amxd(b"too short")


def test_unpack_rejects_bad_magic():
    bogus = b"XXXX" + b"\x00" * 60
    with pytest.raises(PatcherIOError):
        unpack_amxd(bogus)


def test_unpack_rejects_bad_version():
    data = bytearray(pack_amxd('{"x":1}'))
    struct.pack_into("<I", data, 4, 99)  # bump version
    with pytest.raises(PatcherIOError):
        unpack_amxd(bytes(data))


def test_unpack_rejects_missing_ptch_tag():
    data = bytearray(pack_amxd('{"x":1}'))
    data[12:16] = b"XXXX"
    with pytest.raises(PatcherIOError, match="ptch"):
        unpack_amxd(bytes(data))


def test_unpack_rejects_missing_mxac_tag():
    data = bytearray(pack_amxd('{"x":1}'))
    data[20:24] = b"XXXX"
    with pytest.raises(PatcherIOError, match="mx@c"):
        unpack_amxd(bytes(data))


def test_write_and_read_amxd_file(tmp_path):
    path = tmp_path / "test.amxd"
    patcher_dict = {"patcher": {"boxes": [], "lines": [], "rect": [0, 0, 100, 100]}}
    write_amxd(path, patcher_dict)

    raw = path.read_bytes()
    assert raw[0:4] == b"ampf"
    assert raw[12:16] == b"ptch"
    assert raw[20:24] == b"mx@c"

    recovered, device_type = read_amxd(path)
    assert recovered == patcher_dict
    assert device_type == "audio_effect"


def test_patcher_save_amxd_extension(tmp_path):
    path = tmp_path / "device.amxd"
    p = _build_patcher(str(path))
    p.save()

    raw = path.read_bytes()
    assert raw[0:4] == b"ampf"

    loaded = Patcher.from_file(path)
    assert len(loaded._boxes) == 3
    assert len(loaded._lines) == 2


def test_patcher_maxpat_still_plain_json(tmp_path):
    # Regression: .maxpat path must not become binary.
    path = tmp_path / "plain.maxpat"
    p = _build_patcher(str(path))
    p.save()

    raw = path.read_bytes()
    assert raw[0:1] == b"{"
    json.loads(raw)  # parses as JSON


def test_from_file_roundtrip_amxd(tmp_path):
    src = tmp_path / "src.amxd"
    p = _build_patcher(str(src))
    p.save()

    reloaded = Patcher.from_file(src)
    assert len(reloaded._boxes) == 3
    assert len(reloaded._lines) == 2


def test_build_amxd_demo_tone():
    """Drop this file onto Max (File > Open) to verify it loads and plays."""
    path = OUT / "test_amxd_demo_tone.amxd"
    p = Patcher(str(path))
    # Compact canvas (x, y, width, height)
    p.rect = Rect(100.0, 100.0, 260.0, 220.0)

    osc = p.add_textbox("cycle~ 440", patching_rect=[20, 20, 100, 22])
    atten = p.add_textbox("*~ 0.2", patching_rect=[20, 70, 100, 22])
    dac = p.add_textbox("ezdac~", patching_rect=[20, 120, 100, 45])
    p.add_line(osc, atten)
    p.add_line(atten, dac, inlet=0)
    p.add_line(atten, dac, inlet=1)
    p.save()

    raw = path.read_bytes()
    assert raw[0:4] == b"ampf"
    assert raw[12:16] == b"ptch"
    # Round-trips cleanly back through py2max.
    reloaded = Patcher.from_file(path)
    assert len(reloaded._boxes) == 3
    assert len(reloaded._lines) == 3


def test_build_amxd_demo_device():
    """Minimal M4L Audio Effect: plugin~ -> live.gain~ -> plugout~.

    Includes live.thisdevice (device lifecycle) and opens in presentation mode.
    Drop onto an audio track in Ableton Live to verify the device strip
    renders and passes audio through a user-controllable gain fader.
    """
    path = OUT / "test_amxd_demo_device.amxd"
    p = Patcher(str(path))
    p.enable_presentation(devicewidth=120)
    # Compact canvas
    p.rect = Rect(100.0, 100.0, 360.0, 260.0)

    # Required for M4L device lifecycle (fires on init, etc.)
    thisdevice = p.add_textbox("live.thisdevice", patching_rect=[20, 20, 100, 22])

    # Audio bus I/O: plugin~ receives from Live, plugout~ sends back.
    plugin = p.add_textbox("plugin~", patching_rect=[20, 70, 100, 22])
    plugout = p.add_textbox("plugout~", patching_rect=[20, 200, 100, 22])

    # live.gain~ is a native UI object: stereo signal-rate gain + fader/meter.
    gain = p.add(
        "live.gain~",
        maxclass="live.gain~",
        patching_rect=[150, 70, 60, 136],
    )
    gain.add_to_presentation([20, 20, 60, 136])

    # Stereo signal path: plugin~ L/R -> live.gain~ L/R -> plugout~ L/R
    p.add_line(plugin, gain, outlet=0, inlet=0)
    p.add_line(plugin, gain, outlet=1, inlet=1)
    p.add_line(gain, plugout, outlet=0, inlet=0)
    p.add_line(gain, plugout, outlet=1, inlet=1)

    p.save()

    raw = path.read_bytes()
    assert raw[0:4] == b"ampf"
    reloaded = Patcher.from_file(path)
    assert reloaded.openinpresentation == 1
    # Sanity: all four required M4L objects survived the roundtrip.
    classes = {b.maxclass for b in reloaded._boxes}
    texts = {getattr(b, "text", "") for b in reloaded._boxes}
    assert "live.gain~" in classes
    assert any(t.startswith("plugin~") for t in texts)
    assert any(t.startswith("plugout~") for t in texts)
    assert any(t.startswith("live.thisdevice") for t in texts)
    _ = thisdevice  # silence unused


@pytest.mark.parametrize(
    "device_type, expected_tag",
    [
        ("audio_effect", b"aaaa"),
        ("instrument", b"iiii"),
        ("midi_effect", b"mmmm"),
    ],
)
def test_pack_emits_correct_device_tag(device_type, expected_tag):
    data = pack_amxd('{"x":1}', device_type=device_type)
    assert data[8:12] == expected_tag


@pytest.mark.parametrize("device_type", list(DEVICE_TYPES))
def test_roundtrip_preserves_device_type(device_type):
    original = '{"patcher": {"boxes": [], "lines": []}}'
    payload, recovered_type = unpack_amxd(pack_amxd(original, device_type=device_type))
    assert json.loads(payload) == json.loads(original)
    assert recovered_type == device_type


def test_pack_rejects_unknown_device_type():
    with pytest.raises(ValueError, match="unknown device_type"):
        pack_amxd('{"x":1}', device_type="bogus")


def test_unpack_rejects_unknown_device_tag():
    data = bytearray(pack_amxd('{"x":1}'))
    data[8:12] = b"zzzz"
    with pytest.raises(PatcherIOError, match="unknown amxd device-type tag"):
        unpack_amxd(bytes(data))


@pytest.mark.parametrize("device_type", list(DEVICE_TYPES))
def test_write_read_amxd_file_device_type(tmp_path, device_type):
    path = tmp_path / f"{device_type}.amxd"
    patcher_dict = {"patcher": {"boxes": [], "lines": [], "rect": [0, 0, 100, 100]}}
    write_amxd(path, patcher_dict, device_type=device_type)
    recovered, recovered_type = read_amxd(path)
    assert recovered == patcher_dict
    assert recovered_type == device_type


@pytest.mark.parametrize("device_type", list(DEVICE_TYPES))
def test_patcher_save_amxd_with_device_type(tmp_path, device_type):
    path = tmp_path / f"device_{device_type}.amxd"
    p = Patcher(str(path), device_type=device_type)
    p.add_textbox("cycle~ 440")
    p.save()

    raw = path.read_bytes()
    assert raw[8:12] == DEVICE_TYPES[device_type]

    reloaded = Patcher.from_file(path)
    assert reloaded._device_type == device_type


@pytest.mark.parametrize(
    "device_type, expected_amxdtype",
    [
        ("audio_effect", 0x61616161),
        ("instrument", 0x69696969),
        ("midi_effect", 0x6D6D6D6D),
    ],
)
def test_ensure_project_block_injects_correct_amxdtype(device_type, expected_amxdtype):
    pd = {"patcher": {"boxes": [], "lines": []}}
    ensure_amxd_project_block(pd, device_type=device_type, mtime=12345)
    proj = pd["patcher"]["project"]
    assert proj["amxdtype"] == expected_amxdtype
    assert proj["creationdate"] == 12345
    assert proj["modificationdate"] == 12345
    assert proj["contents"] == {"patchers": {}}


def test_ensure_project_block_is_idempotent():
    pd = {"patcher": {"project": {"sentinel": True}}}
    ensure_amxd_project_block(pd, device_type="audio_effect")
    assert pd["patcher"]["project"] == {"sentinel": True}


def test_patcher_save_amxd_includes_project_block(tmp_path):
    path = tmp_path / "device.amxd"
    p = Patcher(str(path), device_type="instrument")
    p.add_textbox("cycle~ 440")
    p.save()

    recovered, _ = read_amxd(path)
    proj = recovered["patcher"]["project"]
    assert proj["amxdtype"] == 0x69696969
    assert proj["contents"] == {"patchers": {}}
    assert proj["devpath"] == "."
