"""Max for Live (.amxd) binary format support.

The on-disk layout was reverse-engineered by comparing two valid Max-exported
devices (``outputs/mydevice.amxd`` and ``outputs/mydevice2.amxd``) byte-by-byte.

A ``.amxd`` file is a 36-byte header followed by NUL-terminated UTF-8 patcher
JSON, followed by an IFF-style dependency-list trailer.

Header (offsets 0-35)::

    offset  size  endian  value                           meaning
    0       4     -       "ampf"                          magic
    4       4     LE u32  4                               format version
    8       4     -       "aaaa"/"iiii"/"mmmm"            M4L device type
    12      4     -       "ptch"                          top-level chunk id
    16      4     LE u32  file_size - 20                  ptch payload size
    20      4     -       "mx@c"                          sub-block id
    24      4     BE u32  16                              constant
    28      4     BE u32  0                               flags
    32      4     BE u32  json_size + 16                  mx@c content size
    36      N+1   -       <utf-8 json>\\x00               JSON, NUL-terminated

Trailer (immediately after the JSON NUL, no padding). Each chunk is
``FOURCC + BE u32 size + payload`` where ``size`` *includes* the 8-byte chunk
header. Container chunks (``dlst``, ``dire``) wrap further chunks in their
payload::

    dlst
      dire
        type  -> "JSON"
        fnam  -> patcher filename, NUL-terminated, padded to 4-byte boundary
        sz32  -> BE u32, JSON byte count including NUL
        of32  -> BE u32, 16   (offset of JSON within mx@c block)
        vers  -> BE u32, 0
        flag  -> BE u32, 17
        mdat  -> BE u32, modification time in Max epoch (1904-01-01 UTC)

Originally tracked at https://github.com/shakfu/py2max/issues/9.
"""

from __future__ import annotations

import json
import struct
import time
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple, Union

from .exceptions import PatcherIOError

if TYPE_CHECKING:
    from .core import Box, Patcher

__all__ = [
    # Binary format
    "pack_amxd",
    "unpack_amxd",
    "read_amxd",
    "write_amxd",
    "ensure_amxd_project_block",
    "DEVICE_TYPES",
    "MAX_EPOCH_OFFSET",
    "unix_to_max_time",
    # Presentation-mode helpers (formerly m4l.py)
    "M4L_PRESENTATION_UI_CLASSES",
    "M4L_INFRASTRUCTURE_CLASSES",
    "M4L_DEVICE_HEIGHT_PX",
    "NonIntegerCoordinateWarning",
    "is_presentation_ui",
    "is_m4l_infrastructure",
    "add_to_presentation",
    "enable_presentation",
    "enforce_integer_coords",
]

_MAGIC = b"ampf"
_VERSION = 4
_PTCH_TAG = b"ptch"
_MXAC_TAG = b"mx@c"
_HEADER_SIZE = 36

_MXAC_CONST = 16
_MXAC_FLAGS = 0
_MXAC_PREAMBLE = 16  # bytes between "mx@c" tag and start of JSON

# Trailer chunk constants observed in Max-exported files.
_OF32_VALUE = 16
_VERS_VALUE = 0
_FLAG_VALUE = 17
_TYPE_PAYLOAD = b"JSON"

# Difference in seconds between the Unix epoch (1970-01-01 UTC) and the
# classic Mac/HFS epoch (1904-01-01 UTC) used by Max for its mdat field
# and creation/modification dates inside the patcher JSON.
MAX_EPOCH_OFFSET = 2_082_844_800

# Max for Live device-type markers at header offset 8.
DEVICE_TYPES: dict[str, bytes] = {
    "audio_effect": b"aaaa",
    "instrument": b"iiii",
    "midi_effect": b"mmmm",
}
_TAG_TO_DEVICE_TYPE: dict[bytes, str] = {v: k for k, v in DEVICE_TYPES.items()}


def unix_to_max_time(unix_seconds: Optional[float] = None) -> int:
    """Convert a Unix timestamp to Max's seconds-since-1904 epoch."""
    if unix_seconds is None:
        unix_seconds = time.time()
    return int(unix_seconds) + MAX_EPOCH_OFFSET


def _amxdtype_for(device_type: str) -> int:
    """Return the project.amxdtype int for a device type.

    The value is the FOURCC tag reinterpreted as a big-endian uint32:
    "aaaa" -> 0x61616161, "iiii" -> 0x69696969, "mmmm" -> 0x6d6d6d6d.
    """
    return struct.unpack(">I", _tag_for(device_type))[0]


def ensure_amxd_project_block(
    patcher_dict: dict,
    device_type: str = "audio_effect",
    mtime: Optional[int] = None,
) -> dict:
    """Ensure the patcher dict carries the embedded ``project`` block Max
    requires for self-contained .amxd devices.

    Without this block, Max emits the diagnostic
    "a project without a name is like a day without sunshine. fatal." when
    loading the device. The block mirrors the one Max emits when exporting a
    device from a project; ``contents.patchers`` is left empty so the device
    is self-contained (no external .maxproj reference).

    Mutates ``patcher_dict['patcher']`` in place if the ``project`` key is
    absent. Returns the same dict for convenience.
    """
    inner = patcher_dict.get("patcher", patcher_dict)
    if "project" in inner:
        return patcher_dict
    if mtime is None:
        mtime = unix_to_max_time()
    inner["project"] = {
        "version": 1,
        "creationdate": mtime,
        "modificationdate": mtime,
        "viewrect": [0.0, 0.0, 300.0, 500.0],
        "autoorganize": 1,
        "hideprojectwindow": 1,
        "showdependencies": 1,
        "autolocalize": 0,
        "contents": {"patchers": {}},
        "layout": {},
        "searchpath": {},
        "detailsvisible": 0,
        "amxdtype": _amxdtype_for(device_type),
        "readonly": 0,
        "devpathtype": 0,
        "devpath": ".",
        "sortmode": 0,
        "viewmode": 0,
        "includepackages": 0,
    }
    return patcher_dict


def _tag_for(device_type: str) -> bytes:
    try:
        return DEVICE_TYPES[device_type]
    except KeyError as e:
        raise ValueError(
            f"unknown device_type {device_type!r}; "
            f"expected one of {sorted(DEVICE_TYPES)}"
        ) from e


def _pad4(payload: bytes) -> bytes:
    """Right-pad a chunk payload with zeros to a 4-byte boundary."""
    extra = (-len(payload)) % 4
    return payload + b"\x00" * extra


def _chunk(tag: bytes, payload: bytes) -> bytes:
    """Build an IFF-style chunk: FOURCC + BE u32 size + payload.

    Size is inclusive of the 8-byte header. Payloads must already be padded.
    """
    if len(tag) != 4:
        raise ValueError(f"chunk tag must be 4 bytes, got {tag!r}")
    size = 8 + len(payload)
    return tag + struct.pack(">I", size) + payload


def _u32_chunk(tag: bytes, value: int) -> bytes:
    return _chunk(tag, struct.pack(">I", value))


def pack_amxd(
    patcher_json: Union[str, bytes],
    *,
    device_type: str = "audio_effect",
    patcher_filename: str = "patcher.maxpat",
    mtime: Optional[int] = None,
) -> bytes:
    """Wrap patcher JSON in the .amxd binary container.

    Args:
        patcher_json: The patcher JSON, as a str or pre-encoded UTF-8 bytes.
        device_type: M4L device type. One of "audio_effect" (default),
            "instrument", or "midi_effect".
        patcher_filename: Filename to embed in the trailer's ``fnam`` chunk.
            Max uses this to resolve the patcher within the surrounding
            project. Defaults to ``"patcher.maxpat"``.
        mtime: Modification time, in Max's seconds-since-1904 epoch. If
            ``None``, the current time is used.
    """
    tag = _tag_for(device_type)
    if isinstance(patcher_json, str):
        json_bytes = patcher_json.encode("utf-8")
    else:
        json_bytes = patcher_json

    json_block = json_bytes + b"\x00"
    mxac_content_size = _MXAC_PREAMBLE + len(json_block)

    if mtime is None:
        mtime = unix_to_max_time()

    fname_payload = _pad4(patcher_filename.encode("utf-8") + b"\x00")
    dire_payload = b"".join(
        [
            _chunk(b"type", _TYPE_PAYLOAD),
            _chunk(b"fnam", fname_payload),
            _u32_chunk(b"sz32", len(json_block)),
            _u32_chunk(b"of32", _OF32_VALUE),
            _u32_chunk(b"vers", _VERS_VALUE),
            _u32_chunk(b"flag", _FLAG_VALUE),
            _u32_chunk(b"mdat", mtime),
        ]
    )
    dlst = _chunk(b"dlst", _chunk(b"dire", dire_payload))

    # Header
    header_top = (
        _MAGIC
        + struct.pack("<I", _VERSION)
        + tag
        + _PTCH_TAG
    )
    # ptch payload starts at offset 20 and runs to end of file.
    ptch_payload_size = (
        4  # "mx@c"
        + 4  # bytes 24-27 (BE 16)
        + 4  # bytes 28-31 (BE 0 flags)
        + 4  # bytes 32-35 (mxac content size)
        + len(json_block)
        + len(dlst)
    )

    mxac_block = (
        _MXAC_TAG
        + struct.pack(">I", _MXAC_CONST)
        + struct.pack(">I", _MXAC_FLAGS)
        + struct.pack(">I", mxac_content_size)
        + json_block
    )

    return (
        header_top
        + struct.pack("<I", ptch_payload_size)
        + mxac_block
        + dlst
    )


def unpack_amxd(data: bytes) -> Tuple[bytes, str]:
    """Extract the patcher JSON payload and device type from an .amxd byte string.

    Returns:
        A ``(payload, device_type)`` tuple where ``payload`` is the raw JSON
        bytes (no trailing NUL) and ``device_type`` is one of "audio_effect",
        "instrument", or "midi_effect".

    Raises:
        PatcherIOError: on an invalid header or unrecognized device tag.
    """
    if len(data) < _HEADER_SIZE:
        raise PatcherIOError(
            f"amxd file too short ({len(data)} bytes, need >= {_HEADER_SIZE})",
            operation="read",
        )

    if data[0:4] != _MAGIC:
        raise PatcherIOError(
            f"not an amxd file (magic={data[0:4]!r}, expected {_MAGIC!r})",
            operation="read",
        )

    version = struct.unpack("<I", data[4:8])[0]
    if version != _VERSION:
        raise PatcherIOError(
            f"unsupported amxd version {version} (expected {_VERSION})",
            operation="read",
        )

    tag = data[8:12]
    device_type = _TAG_TO_DEVICE_TYPE.get(tag)
    if device_type is None:
        raise PatcherIOError(
            f"unknown amxd device-type tag {tag!r} at offset 8 "
            f"(expected one of {sorted(DEVICE_TYPES.values())})",
            operation="read",
        )

    if data[12:16] != _PTCH_TAG:
        raise PatcherIOError(
            f"missing ptch tag at offset 12 (got {data[12:16]!r})",
            operation="read",
        )

    if data[20:24] != _MXAC_TAG:
        raise PatcherIOError(
            f"missing mx@c tag at offset 20 (got {data[20:24]!r})",
            operation="read",
        )

    mxac_content_size = struct.unpack(">I", data[32:36])[0]
    if mxac_content_size < _MXAC_PREAMBLE + 1:
        raise PatcherIOError(
            f"mx@c content size too small ({mxac_content_size})",
            operation="read",
        )
    json_block_len = mxac_content_size - _MXAC_PREAMBLE
    json_end_excl_nul = _HEADER_SIZE + json_block_len - 1
    if json_end_excl_nul > len(data):
        raise PatcherIOError(
            f"declared JSON length runs past end of file "
            f"({json_end_excl_nul} > {len(data)})",
            operation="read",
        )

    json_bytes = data[_HEADER_SIZE:json_end_excl_nul]
    return json_bytes, device_type


def read_amxd(path: Union[str, Path]) -> Tuple[dict, str]:
    """Read an .amxd file.

    Returns:
        A ``(patcher_dict, device_type)`` tuple.
    """
    path = Path(path)
    try:
        data = path.read_bytes()
    except OSError as e:
        raise PatcherIOError(
            f"failed to read amxd file: {path}", file_path=str(path), operation="read"
        ) from e

    payload, device_type = unpack_amxd(data)
    return json.loads(payload), device_type


def write_amxd(
    path: Union[str, Path],
    patcher_dict: dict,
    *,
    device_type: str = "audio_effect",
    patcher_filename: Optional[str] = None,
    mtime: Optional[int] = None,
) -> None:
    """Serialize a patcher dict and write it as a .amxd file.

    Args:
        path: Output path.
        patcher_dict: Patcher dict (the same shape as a .maxpat JSON).
        device_type: M4L device type. One of "audio_effect" (default),
            "instrument", or "midi_effect".
        patcher_filename: Filename to embed in the ``fnam`` trailer chunk.
            Defaults to the output path's stem with a ``.maxpat`` extension.
        mtime: Modification time in Max's seconds-since-1904 epoch.
            Defaults to the current time.
    """
    path = Path(path)
    if patcher_filename is None:
        patcher_filename = path.stem + ".maxpat"
    ensure_amxd_project_block(patcher_dict, device_type=device_type, mtime=mtime)
    payload = json.dumps(patcher_dict, indent=4)
    data = pack_amxd(
        payload,
        device_type=device_type,
        patcher_filename=patcher_filename,
        mtime=mtime,
    )
    try:
        if path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except OSError as e:
        raise PatcherIOError(
            f"failed to write amxd file: {path}",
            file_path=str(path),
            operation="write",
        ) from e


# ===========================================================================
# Max for Live (M4L) presentation-mode helpers
#
# M4L devices live in a fixed-size device strip in Ableton Live. The patcher
# renders in *presentation mode* (not patching mode), so each UI object must
# be explicitly marked with ``presentation=1`` and given a ``presentation_rect``.
# Infrastructure objects (``live.remote~``, ``live.map``, etc.) stay hidden.
#
# Constraints imposed by Live's device view:
# - Device strip height is fixed at ~170 px by the host.
# - Coordinates should be whole integers; fractional values render blurry on
#   non-retina displays.
# - ``devicewidth`` on the patcher controls the device strip width.
# ===========================================================================


# ---------------------------------------------------------------------------
# Object classification for presentation-mode filtering
#
# Only user-facing controls belong in the device strip. Infrastructure
# objects (Live API bridges, routing, device lifecycle) stay in the patcher
# but must not get presentation=1.

M4L_PRESENTATION_UI_CLASSES: frozenset = frozenset(
    {
        "live.dial",
        "live.numbox",
        "live.slider",
        "live.menu",
        "live.tab",
        "live.text",
        "live.toggle",
        "live.button",
        "live.comment",
        "live.gain~",
        "live.step",
        "live.grid",
        "live.meter~",
        "live.scope~",
        # Classic (non-live.*) UI that also works in presentation
        "dial",
        "number",
        "flonum",
        "toggle",
        "button",
        "comment",
        "panel",
        "umenu",
        "slider",
    }
)

M4L_INFRASTRUCTURE_CLASSES: frozenset = frozenset(
    {
        "live.remote~",
        "live.map",
        "live.object",
        "live.path",
        "live.observer",
        "live.thisdevice",
        "live.banks",
        "live.parameter",
    }
)

# Ableton's device view height is fixed; devicewidth is the one dim you set.
M4L_DEVICE_HEIGHT_PX = 170


# ---------------------------------------------------------------------------
# Integer-coordinate guardrail


class NonIntegerCoordinateWarning(UserWarning):
    """Emitted when a rect contains fractional coordinates."""


def _to_int_rect(
    rect: Iterable[Union[int, float]], *, context: str
) -> List[int]:
    """Coerce a 4-tuple rect to ints, warning on non-integer inputs."""
    values = list(rect)
    if len(values) != 4:
        raise ValueError(f"rect must have 4 elements, got {len(values)}: {values}")

    rounded = []
    had_float = False
    for v in values:
        if isinstance(v, float) and not v.is_integer():
            had_float = True
        rounded.append(int(round(float(v))))

    if had_float:
        warnings.warn(
            f"M4L: non-integer coords in {context} {values} -> {rounded}; "
            "Ableton renders decimals blurry on non-retina.",
            NonIntegerCoordinateWarning,
            stacklevel=3,
        )
    return rounded


# ---------------------------------------------------------------------------
# Classification helpers


def _object_name(box: "Box") -> str:
    """Resolve the effective object name for classification.

    Native-maxclass objects (live.dial, toggle, etc.) carry the name in
    ``maxclass``. ``newobj`` boxes carry it as the first token of ``text``.
    """
    if box.maxclass and box.maxclass != "newobj":
        return box.maxclass
    text = getattr(box, "text", "") or ""
    return text.split()[0] if text else box.maxclass or ""


def is_presentation_ui(box: "Box") -> bool:
    """True if the box is a user-facing control suitable for presentation."""
    return _object_name(box) in M4L_PRESENTATION_UI_CLASSES


def is_m4l_infrastructure(box: "Box") -> bool:
    """True if the box is M4L infrastructure that must stay hidden."""
    return _object_name(box) in M4L_INFRASTRUCTURE_CLASSES


# ---------------------------------------------------------------------------
# Presentation-mode public API


def add_to_presentation(
    box: "Box",
    rect: Union[Iterable[Union[int, float]], Tuple[int, int, int, int]],
    *,
    strict: bool = False,
) -> "Box":
    """Mark a box as a presentation-mode UI element.

    Sets ``presentation=1`` and ``presentation_rect=[x, y, w, h]``. Rounds
    fractional coordinates to integers with a warning. Refuses known
    infrastructure objects (``live.remote~`` etc.), which must not appear in
    the device strip.

    Args:
        box: the Box to expose in presentation mode.
        rect: [x, y, width, height] in device-strip coordinates.
        strict: if True, warn when the box is not a recognized UI class.
            Useful to catch typos early; defaults to False so user-defined
            or unusual UI objects still work.
    """
    if is_m4l_infrastructure(box):
        raise ValueError(
            f"refusing to add {_object_name(box)!r} to presentation: it is "
            "M4L infrastructure and must stay hidden from the device strip."
        )

    if strict and not is_presentation_ui(box):
        warnings.warn(
            f"M4L: {_object_name(box)!r} is not a known presentation UI class; "
            "it may still work but is unusual in a device strip.",
            UserWarning,
            stacklevel=2,
        )

    int_rect = _to_int_rect(rect, context=f"{_object_name(box)} presentation_rect")

    # These are patcher-level attributes on the box dict.
    box.presentation = 1  # type: ignore[attr-defined]
    box.presentation_rect = int_rect  # type: ignore[attr-defined]
    return box


def enable_presentation(
    patcher: "Patcher",
    devicewidth: Union[int, None] = None,
) -> "Patcher":
    """Configure a patcher to open in presentation mode as an M4L device.

    Sets ``openinpresentation=1`` and optionally ``devicewidth`` (px).
    Ableton's device strip height is fixed at ~170 px; only width is
    author-controlled.
    """
    patcher.openinpresentation = 1  # type: ignore[attr-defined]
    if devicewidth is not None:
        patcher.devicewidth = int(round(devicewidth))  # type: ignore[attr-defined]
    return patcher


def enforce_integer_coords(patcher: "Patcher") -> int:
    """Walk a patcher and round all rect coords to integers.

    Returns the number of rects that were non-integer (and got rounded).
    Recurses into nested subpatchers.
    """
    def _round_rect(rect):
        """Round a rect in-place. Returns 1 if any coord was non-integer."""
        # Rect dataclass with .x/.y/.w/.h or a plain [x,y,w,h] list.
        if hasattr(rect, "x"):
            coords = [rect.x, rect.y, rect.w, rect.h]
            if any(isinstance(v, float) and not v.is_integer() for v in coords):
                rect.x, rect.y, rect.w, rect.h = (int(round(v)) for v in coords)
                return 1
        elif isinstance(rect, list):
            if any(isinstance(v, float) and not v.is_integer() for v in rect):
                rect[:] = [int(round(v)) for v in rect]
                return 1
        return 0

    changed = 0
    for box in patcher._boxes:
        pr = getattr(box, "patching_rect", None)
        if pr is not None:
            changed += _round_rect(pr)

        if hasattr(box, "presentation_rect"):
            changed += _round_rect(box.presentation_rect)

        sub = getattr(box, "_patcher", None)
        if sub is not None:
            changed += enforce_integer_coords(sub)

    return changed
