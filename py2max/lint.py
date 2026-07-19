"""Patch-level linting: structural and connection health checks.

``lint(patcher)`` returns a list of :class:`Finding`s -- errors and warnings --
covering connection validity, out-of-range ports, orphaned patchlines,
duplicate IDs, overlapping objects, off-canvas objects, and unknown object
classes. It is the productized form of the ad-hoc checks that repeatedly caught
real bugs, and the basis for on-by-default checking on ``save()``.

Only the top-level patcher is linted; nested subpatchers have their own
coordinate space and are left to a future recursive pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from .maxref import get_object_info
from .maxref import porttypes
from .utils import object_name

# --- severities ---
ERROR = "error"
WARNING = "warning"

# --- finding codes ---
E_DUP_ID = "E-DUP-ID"
E_ORPHAN_LINE = "E-ORPHAN-LINE"
E_OUTLET_RANGE = "E-OUTLET-RANGE"
E_INLET_RANGE = "E-INLET-RANGE"
E_BAD_CONNECTION = "E-BAD-CONNECTION"
W_OVERLAP = "W-OVERLAP"
W_OFFCANVAS = "W-OFFCANVAS"
W_UNKNOWN_OBJECT = "W-UNKNOWN-OBJECT"


@dataclass
class Finding:
    """A single lint result."""

    code: str
    severity: str
    message: str
    obj_id: Optional[str] = None
    #: (src_id, outlet, dst_id, inlet) for connection findings
    line: Optional[Tuple[str, int, str, int]] = None

    def __str__(self) -> str:
        where = ""
        if self.line is not None:
            s, so, d, di = self.line
            where = f" [{s}:{so} -> {d}:{di}]"
        elif self.obj_id is not None:
            where = f" [{self.obj_id}]"
        return f"{self.severity.upper()} {self.code}: {self.message}{where}"


def _overlap(a: Any, b: Any) -> bool:
    return bool(
        a[0] < b[0] + b[2]
        and b[0] < a[0] + a[2]
        and a[1] < b[1] + b[3]
        and b[1] < a[1] + a[3]
    )


def _port(pair: Any, idx: int) -> int:
    """Second element of a source/destination pair, defaulting to 0."""
    return int(pair[idx]) if len(pair) > idx else 0


def _effective_counts(box: Any, name: str) -> Tuple[Optional[int], Optional[int]]:
    """(inlet_count, outlet_count) for a box, subpatcher-aware."""
    sub_in, sub_out = porttypes.subpatcher_counts(box)
    n_in, n_out = porttypes.port_counts(name, getattr(box, "text", None))
    return (
        sub_in if sub_in is not None else n_in,
        sub_out if sub_out is not None else n_out,
    )


def lint(patcher: Any) -> List[Finding]:
    """Return all lint findings for ``patcher`` and its subpatchers, errors first."""
    findings: List[Finding] = []
    _lint_level(patcher, findings, path="")
    findings.sort(key=lambda f: 0 if f.severity == ERROR else 1)
    return findings


def _lint_level(patcher: Any, findings: List[Finding], path: str) -> None:
    """Lint one patcher level; recurse into subpatchers.

    ``path`` prefixes object ids so a finding inside ``p sub`` is reported as
    ``sub-box-id/obj-1`` rather than an ambiguous ``obj-1``.
    """

    def qid(box_id: str) -> str:
        return f"{path}{box_id}"

    boxes = list(patcher._boxes)
    by_id: dict[str, Any] = {}

    # duplicate IDs
    for b in boxes:
        if b.id in by_id:
            findings.append(
                Finding(
                    E_DUP_ID, ERROR, f"duplicate object id {b.id!r}", obj_id=qid(b.id)
                )
            )
        else:
            by_id[b.id] = b

    # unknown object classes
    for b in boxes:
        name = object_name(b)
        if name and get_object_info(name) is None:
            findings.append(
                Finding(
                    W_UNKNOWN_OBJECT,
                    WARNING,
                    f"object {name!r} is not in the Max reference",
                    obj_id=qid(b.id),
                )
            )

    # off-canvas: object extends outside the patcher window
    rect = patcher.rect
    win_w, win_h = float(rect[2]), float(rect[3])
    for b in boxes:
        r = b.patching_rect
        x, y, w, h = float(r[0]), float(r[1]), float(r[2]), float(r[3])
        if x < 0 or y < 0 or x + w > win_w or y + h > win_h:
            findings.append(
                Finding(
                    W_OFFCANVAS,
                    WARNING,
                    f"object {b.id!r} extends outside the patcher window "
                    f"({win_w:.0f}x{win_h:.0f})",
                    obj_id=qid(b.id),
                )
            )

    # overlaps (dimension-aware)
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if _overlap(boxes[i].patching_rect, boxes[j].patching_rect):
                findings.append(
                    Finding(
                        W_OVERLAP,
                        WARNING,
                        f"objects {boxes[i].id!r} and {boxes[j].id!r} overlap",
                        obj_id=qid(boxes[i].id),
                    )
                )

    # patchlines: orphans, out-of-range ports, message-type compatibility
    for pl in patcher._lines:
        src_id, outlet = pl.source[0], _port(pl.source, 1)
        dst_id, inlet = pl.destination[0], _port(pl.destination, 1)
        line = (qid(src_id), outlet, qid(dst_id), inlet)
        sb, db = by_id.get(src_id), by_id.get(dst_id)
        if sb is None or db is None:
            findings.append(
                Finding(
                    E_ORPHAN_LINE,
                    ERROR,
                    "patchline references a missing object",
                    line=line,
                )
            )
            continue

        src_name, dst_name = object_name(sb), object_name(db)
        _, n_out = _effective_counts(sb, src_name)
        n_in, _ = _effective_counts(db, dst_name)
        if n_out is not None and outlet >= n_out:
            findings.append(
                Finding(
                    E_OUTLET_RANGE,
                    ERROR,
                    f"{src_name!r} has {n_out} outlet(s); outlet {outlet} is out of range",
                    line=line,
                )
            )
            continue
        if n_in is not None and inlet >= n_in:
            findings.append(
                Finding(
                    E_INLET_RANGE,
                    ERROR,
                    f"{dst_name!r} has {n_in} inlet(s); inlet {inlet} is out of range",
                    line=line,
                )
            )
            continue

        emit = porttypes.outlet_emits(src_name, outlet)
        accepts, authoritative = porttypes.inlet_acceptance(dst_name, inlet)
        bang_reject = emit == porttypes.BANG and porttypes.inlet_rejects_bang(
            dst_name, inlet
        )
        if (
            bang_reject
            or porttypes.message_compatible(emit, accepts, authoritative) is False
        ):
            findings.append(
                Finding(
                    E_BAD_CONNECTION,
                    ERROR,
                    f"cannot connect {emit} outlet {outlet} of {src_name!r} "
                    f"to inlet {inlet} of {dst_name!r}",
                    line=line,
                )
            )

    # recurse into subpatchers (each has its own coordinate space)
    for b in boxes:
        child = getattr(b, "_patcher", None)
        if child is not None:
            _lint_level(child, findings, path=f"{path}{b.id}/")


def has_errors(findings: List[Finding]) -> bool:
    """True if any finding is error-severity."""
    return any(f.severity == ERROR for f in findings)
