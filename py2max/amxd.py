"""Max for Live (.amxd) binary format support.

An .amxd file is a 24-byte header followed by a ``ptch`` chunk wrapping the
patcher JSON (the same JSON payload as a ``.maxpat`` file).

Header layout (little-endian, 32 bytes total before JSON)::

    offset  size  bytes           meaning
    0       4     "ampf"          magic
    4       4     04 00 00 00     format version (uint32 LE, = 4)
    8       4     "aaaa"          padding
    12      4     "meta"          chunk tag
    16      4     04 00 00 00     meta chunk size (uint32 LE, = 4)
    20      4     00 00 00 00     meta chunk payload (4 zero bytes)
    24      4     "ptch"          chunk tag
    28      4     <uint32 LE>     JSON byte length
    32      N     <bytes>         UTF-8 JSON

Reverse-engineered and documented by @williamfrench95
https://github.com/shakfu/py2max/issues/9.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Union

from .exceptions import PatcherIOError

__all__ = ["pack_amxd", "unpack_amxd", "read_amxd", "write_amxd"]

_MAGIC = b"ampf"
_VERSION = 4
_PAD = b"aaaa"
_META_TAG = b"meta"
_META_SIZE = 4
_META_PAYLOAD = b"\x00\x00\x00\x00"
_PTCH_TAG = b"ptch"
_HEADER_SIZE = 32


def pack_amxd(patcher_json: Union[str, bytes]) -> bytes:
    """Wrap patcher JSON in the .amxd binary container."""
    if isinstance(patcher_json, str):
        payload = patcher_json.encode("utf-8")
    else:
        payload = patcher_json

    header = b"".join(
        [
            _MAGIC,
            struct.pack("<I", _VERSION),
            _PAD,
            _META_TAG,
            struct.pack("<I", _META_SIZE),
            _META_PAYLOAD,
            _PTCH_TAG,
            struct.pack("<I", len(payload)),
        ]
    )
    assert len(header) == _HEADER_SIZE
    return header + payload


def unpack_amxd(data: bytes) -> bytes:
    """Extract the patcher JSON payload from an .amxd byte string.

    Raises PatcherIOError on an invalid header. Tolerates a wrong declared
    length by falling back to a brace-balanced scan of the payload.
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

    if data[24:28] != _PTCH_TAG:
        raise PatcherIOError(
            f"missing ptch tag at offset 24 (got {data[24:28]!r})",
            operation="read",
        )

    declared_len = struct.unpack("<I", data[28:32])[0]
    body = data[_HEADER_SIZE:]

    if declared_len <= len(body):
        candidate = body[:declared_len]
        # Sanity check: must be valid JSON.
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass

    # Fallback: scan from first '{' to its matching '}' (string-aware).
    return _extract_json_by_braces(body)


def _extract_json_by_braces(body: bytes) -> bytes:
    start = body.find(b"{")
    if start < 0:
        raise PatcherIOError("no JSON object found in amxd payload", operation="read")

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(body)):
        c = body[i : i + 1]
        if in_string:
            if escape:
                escape = False
            elif c == b"\\":
                escape = True
            elif c == b'"':
                in_string = False
            continue
        if c == b'"':
            in_string = True
        elif c == b"{":
            depth += 1
        elif c == b"}":
            depth -= 1
            if depth == 0:
                return body[start : i + 1]

    raise PatcherIOError("unterminated JSON object in amxd payload", operation="read")


def read_amxd(path: Union[str, Path]) -> dict:
    """Read an .amxd file and return the parsed patcher JSON as a dict."""
    path = Path(path)
    try:
        data = path.read_bytes()
    except OSError as e:
        raise PatcherIOError(
            f"failed to read amxd file: {path}", file_path=str(path), operation="read"
        ) from e

    payload = unpack_amxd(data)
    return json.loads(payload)


def write_amxd(path: Union[str, Path], patcher_dict: dict) -> None:
    """Serialize a patcher dict and write it as a .amxd file."""
    path = Path(path)
    payload = json.dumps(patcher_dict, indent=4)
    data = pack_amxd(payload)
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
