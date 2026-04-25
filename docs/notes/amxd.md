# Max for Live (`.amxd`) Implementation Notes

Implements [issue #9](https://github.com/shakfu/py2max/issues/9). Initial framing was based on @williamfrench95's reverse-engineering notes. The initial implementation didn't produce a valid .amxd file as evidenced by a funny error raised in Max about a missing 'name'.

This provided a hint that a project had to be in the picture and the on-disk layout was then re-derived byte-by-byte against two minimal real Max-exported devices (`outputs/mydevice.amxd`, `outputs/mydevice2.amxd`) to produce files that load cleanly in Live.

All public symbols live in `py2max.m4l`.

## On-Disk Format

A `.amxd` file is a 36-byte header followed by NUL-terminated UTF-8 patcher JSON, followed by an IFF-style dependency-list trailer.

### Header (offsets 0-35)

```
offset  size  endian  value                           meaning
0       4     -       "ampf"                          magic
4       4     LE u32  4                               format version
8       4     -       "aaaa" / "iiii" / "mmmm"        M4L device type
12      4     -       "ptch"                          top-level chunk id
16      4     LE u32  file_size - 20                  ptch payload size
20      4     -       "mx@c"                          sub-block id
24      4     BE u32  16                              constant
28      4     BE u32  0                               flags
32      4     BE u32  json_size + 16                  mx@c content size
36      N+1   -       <utf-8 json>\x00                JSON, NUL-terminated
```

Notes:
- The `ptch` chunk size at offset 16 is **little-endian**; every other size in the file is **big-endian**.
- The 4 bytes at offset 8 are the device-type tag, *not* padding (this differed from the original issue #9 notes).

### Trailer

Immediately after the JSON's NUL byte, no padding. Each chunk is `FOURCC + BE u32 size + payload` where `size` is **inclusive** of the 8-byte chunk header. Container chunks (`dlst`, `dire`) wrap further chunks in their payload.

```
dlst
  dire
    type  -> "JSON"                            (4-byte payload, constant)
    fnam  -> patcher filename                  (NUL-terminated, padded to 4-byte boundary)
    sz32  -> BE u32, JSON byte count incl. NUL
    of32  -> BE u32, 16                        (offset of JSON within mx@c block)
    vers  -> BE u32, 0                         (constant)
    flag  -> BE u32, 17                        (constant)
    mdat  -> BE u32, modification time         (Max epoch, see below)
```

### Max Epoch

Timestamps in `mdat` and inside the embedded `project` block (`creationdate`, `modificationdate`) are seconds since 1904-01-01 UTC (classic Mac/HFS epoch). Convert with `unix_to_max_time(unix_seconds)` or the constant `MAX_EPOCH_OFFSET = 2_082_844_800`.

## Embedded `project` Block

Without a `project` dict inside the patcher JSON, Max emits the cryptic diagnostic:

> "a project without a name is like a day without sunshine. fatal."

The error mentions a *name* but neither real fixture has a `name` field — what Max actually requires is the whole `project` block. `ensure_amxd_project_block` injects it when missing, using the same shape Max emits when exporting a device from a real `.maxproj`:

```python
{
    "version": 1,
    "creationdate": <mtime>,
    "modificationdate": <mtime>,
    "viewrect": [0.0, 0.0, 300.0, 500.0],
    "autoorganize": 1,
    "hideprojectwindow": 1,
    "showdependencies": 1,
    "autolocalize": 0,
    "contents": {"patchers": {}},   # self-contained — no external .maxproj reference
    "layout": {},
    "searchpath": {},
    "detailsvisible": 0,
    "amxdtype": <device tag as BE u32>,
    "readonly": 0,
    "devpathtype": 0,
    "devpath": ".",
    "sortmode": 0,
    "viewmode": 0,
    "includepackages": 0,
}
```

`amxdtype` is the FOURCC device tag reinterpreted as a big-endian uint32:

| Device type   | Tag    | `amxdtype`   |
| ------------- | ------ | ------------ |
| Audio Effect  | `aaaa` | `0x61616161` |
| Instrument    | `iiii` | `0x69696969` |
| MIDI Effect   | `mmmm` | `0x6d6d6d6d` |

The helper is **idempotent** — a pre-existing `project` block is left untouched, so byte-for-byte round-trips against real Max-exported fixtures still pass.

## Fields That Vary vs Constants

Comparing `outputs/mydevice.amxd` and `outputs/mydevice2.amxd`:

| Field                          | Source                                     |
| ------------------------------ | ------------------------------------------ |
| `ptch` chunk size (offset 16)  | `file_size - 20`                           |
| `sz32` payload                 | JSON byte count including trailing NUL     |
| `fnam` payload                 | patcher filename (NUL + 4-byte pad)        |
| `mdat` payload                 | modification time in Max epoch             |
| JSON content                   | the patcher JSON (incl. `project.creationdate`/`modificationdate` which match `mdat`) |

Everything else in the header and trailer is constant for our purposes:
`ampf`, version `4`, `ptch`, `mx@c`, the BE constants `16` / `0` at offsets 24/28, `of32 = 16`, `vers = 0`, `flag = 17`, `type = "JSON"`, and all FOURCC tags.

## Public API (`py2max.m4l`)

Binary format:
- `pack_amxd(json, *, device_type, patcher_filename, mtime)` -> `bytes`
- `unpack_amxd(data)` -> `(json_bytes, device_type)`
- `read_amxd(path)` -> `(patcher_dict, device_type)`
- `write_amxd(path, dict, *, device_type, patcher_filename, mtime)`
- `ensure_amxd_project_block(patcher_dict, device_type, mtime)`
- `unix_to_max_time(unix_seconds=None)` -> `int`
- `DEVICE_TYPES`, `MAX_EPOCH_OFFSET`

Patcher integration:
- `Patcher(path, device_type="audio_effect", ...)`
- `Patcher.save()` and `Patcher.from_file()` auto-detect the `.amxd` extension; `.maxpat` paths are unchanged.

Presentation-mode helpers (also in `py2max.m4l`):
- `Patcher.enable_presentation(devicewidth=...)`, `Patcher.enforce_integer_coords()`
- `Box.add_to_presentation([x, y, w, h], *, strict=False)`
- `is_presentation_ui(box)`, `is_m4l_infrastructure(box)`
- `M4L_PRESENTATION_UI_CLASSES`, `M4L_INFRASTRUCTURE_CLASSES`, `NonIntegerCoordinateWarning`

## Verification

`tests/test_amxd.py::test_pack_byte_for_byte_matches_max_export` re-packs the JSON extracted from each real Max-exported `.amxd` with the original `fnam` and `mdat`, and asserts the output matches the original file byte-for-byte. Runs against both fixtures.

Verified by loading into Max 9 and the the device loads with any errors.

