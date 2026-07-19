"""Port message-type model for connection validation.

maxref's per-port ``type`` field is reliable for MSP signal ports (``signal`` /
``signal/float``) but not for control ports -- most carry a placeholder
(``INLET_TYPE`` / ``OUTLET_TYPE``) because the ``.maxref.xml`` only annotates
signal typing. Object I/O that depends on arguments (``limi~ 2``) or on content
(``bpatcher``, subpatchers) is not modeled at all.

This module normalizes port typing into a small set of *message kinds* and
layers curated overrides for the objects maxref gets wrong, so validation can be
accurate on the cases we are confident about and **permissive** (skip) on the
rest. Being permissive on unknowns is deliberate: on-by-default validation must
not raise on valid patches, so a false negative is preferable to a false
positive.
"""

from __future__ import annotations

import re
from typing import FrozenSet, List, Optional, Tuple

from .parser import get_object_info

_Counts = Tuple[Optional[int], Optional[int]]

# --- message kinds ---------------------------------------------------------
SIGNAL = "signal"  # MSP audio signal
BANG = "bang"
INT = "int"
FLOAT = "float"
LIST = "list"
ANY = "any"  # unknown control inlet/outlet -> treat permissively

_PLACEHOLDERS = {"", "inlet_type", "outlet_type"}


# --- curated overrides -----------------------------------------------------
# Outlets that emit a specific control message (maxref reports a placeholder).
# Keyed by maxclass -> {outlet_index: kind}. Kept small and high-confidence.
_OUTLET_EMIT = {
    "metro": {0: BANG},
    "tempo": {0: BANG},
    "loadbang": {0: BANG},
    "button": {0: BANG},  # the bng UI object
    "bangbang": {0: BANG, 1: BANG},
    "flonum": {0: FLOAT},
    "number": {0: INT},
    "toggle": {0: INT},
}

# Inlets maxref mis-types as control that are really signal-only. Keyed by
# maxclass -> {inlet_index: accept-set}.
_INLET_ACCEPTS = {
    "noise~": {0: frozenset({SIGNAL})},
    "pink~": {0: frozenset({SIGNAL})},
}

# Signal/float inlets on pure DSP objects that do NOT accept a bang (unlike
# envelope/ramp objects such as adsr~ / line~, whose signal/float inlet *is*
# bang-triggerable). Keyed by maxclass -> set of inlet indices. A bang into one
# of these is a definite error; this lets us catch e.g. metro -> cycle~ without
# false-positiving adsr~.
_SIGNAL_INLET_REJECTS_BANG = {
    "cycle~": {0, 1},
    "saw~": {0, 1},
    "tri~": {0, 1, 2},
    "rect~": {0, 1, 2},
    "phasor~": {0},
    "+~": {0, 1},
    "*~": {0, 1},
    "-~": {0, 1},
    "/~": {0, 1},
}


def _args(text: Optional[str]) -> List[str]:
    """Tokens after the object name in a box's ``text``."""
    return text.split()[1:] if text else []


def _first_int(args: List[str]) -> Optional[int]:
    for tok in args:
        if re.fullmatch(r"-?\d+", tok):
            return int(tok)
    return None


# Per-object port-count resolvers. Each maps the argument tokens to
# ``(n_inlets, n_outlets)``; ``None`` for a dimension means "use the maxref
# default". Two common families: counts that scale with a leading integer *value*
# (``limi~ 2`` -> 2), and counts that scale with the *number* of arguments
# (``select a b c`` -> 4 outlets = args + 1 reject outlet).
def _scale_value_both(a: List[str]) -> _Counts:
    n = _first_int(a)
    return (n, n) if n and n > 0 else (None, None)


def _scale_value_out(a: List[str]) -> _Counts:
    n = _first_int(a)
    return (None, n) if n and n > 0 else (None, None)


def _selector_counts(a: List[str]) -> _Counts:
    n = _first_int(a)  # selector~ N: N signal inlets + 1 control inlet, 1 outlet
    return (n + 1, None) if n and n > 0 else (None, None)


def _switch_counts(a: List[str]) -> _Counts:
    n = _first_int(a)  # switch N: N signal inlets + 1 control inlet, 1 outlet
    return (n + 1, None) if n and n > 0 else (None, None)


def _select_counts(a: List[str]) -> _Counts:
    return (None, len(a) + 1) if a else (None, None)  # match outlets + 1 reject


def _unpack_counts(a: List[str]) -> _Counts:
    return (None, len(a)) if a else (None, None)


def _pack_counts(a: List[str]) -> _Counts:
    return (len(a), None) if a else (None, None)


_ARG_RESOLVERS = {
    "limi~": _scale_value_both,
    "matrix~": _scale_value_both,
    "mc.pack~": _scale_value_out,
    "gate": _scale_value_out,
    "selector~": _selector_counts,
    "switch": _switch_counts,
    "select": _select_counts,
    "sel": _select_counts,
    "route": _select_counts,  # N match outlets + 1 passthrough
    "unpack": _unpack_counts,
    "pack": _pack_counts,
}


def _accepts_from_type(type_str: str) -> FrozenSet[str]:
    """Classify a maxref inlet ``type`` string into an accept-set."""
    t = (type_str or "").strip().lower()
    if t in _PLACEHOLDERS:
        return frozenset({ANY})
    has_signal = "signal" in t
    has_number = "float" in t or "int" in t
    if has_signal and has_number:
        return frozenset({SIGNAL, FLOAT, INT})
    if has_signal:
        return frozenset({SIGNAL})  # signal-only inlet
    kinds = set()
    if "bang" in t:
        kinds.add(BANG)
    if "float" in t:
        kinds.add(FLOAT)
    if "int" in t:
        kinds.add(INT)
    if "list" in t:
        kinds.add(LIST)
    return frozenset(kinds) if kinds else frozenset({ANY})


def _emit_from_type(type_str: str) -> str:
    """Classify a maxref outlet ``type`` string into a single emitted kind."""
    t = (type_str or "").strip().lower()
    if "signal" in t:
        return SIGNAL
    return ANY  # control outlet -- unknown unless curated


# --- public API ------------------------------------------------------------
def port_counts(
    maxclass: str, text: Optional[str] = None
) -> tuple[Optional[int], Optional[int]]:
    """Return ``(inlet_count, outlet_count)`` for an object, arg-aware.

    Uses the leading integer argument for objects whose I/O scales with it
    (``limi~ 2`` -> 2 in / 2 out), otherwise the maxref default. ``None`` for a
    dimension means "unknown" (skip range checks).
    """
    info = get_object_info(maxclass)
    n_in = len(info["inlets"]) if info and "inlets" in info else None
    n_out = len(info["outlets"]) if info and "outlets" in info else None
    resolver = _ARG_RESOLVERS.get(maxclass)
    if resolver is not None:
        r_in, r_out = resolver(_args(text))
        if r_in is not None:
            n_in = r_in
        if r_out is not None:
            n_out = r_out
    return n_in, n_out


def subpatcher_counts(box: object) -> _Counts:
    """Port counts for a subpatcher/bpatcher box, from its nested patcher.

    A subpatcher's real inlet/outlet count is the number of ``inlet`` / ``outlet``
    objects it contains, not the maxref default. Returns ``(None, None)`` for a
    box with no nested patcher.
    """
    child = getattr(box, "_patcher", None)
    if child is None:
        return (None, None)
    from ..utils import object_name

    boxes = getattr(child, "_boxes", [])
    n_in = sum(1 for b in boxes if object_name(b) == "inlet")
    n_out = sum(1 for b in boxes if object_name(b) == "outlet")
    return (n_in, n_out)


def outlet_emits(maxclass: str, index: int) -> str:
    """Message kind emitted by ``maxclass``'s outlet ``index`` (``ANY`` if unsure)."""
    override = _OUTLET_EMIT.get(maxclass, {}).get(index)
    if override is not None:
        return override
    info = get_object_info(maxclass)
    outlets = info.get("outlets", []) if info else []
    if 0 <= index < len(outlets):
        return _emit_from_type(outlets[index].get("type", ""))
    return ANY


# maxref <methodlist> message names -> message kinds
_METHOD_TO_KIND = {
    "signal": SIGNAL,
    "bang": BANG,
    "int": INT,
    "float": FLOAT,
    "list": LIST,
}


def _accepts_from_methods(maxclass: str) -> Optional[FrozenSet[str]]:
    """Accept-set derived from an object's ``<methodlist>``, or ``None``.

    The method list is the object's real message vocabulary (Max's own docs).
    An ``anything`` method is a wildcard -> the inlet takes anything. Objects
    with no method list (e.g. ``+~``, ``noise~``) return ``None`` so the caller
    falls back to the type attribute / curated overrides.
    """
    info = get_object_info(maxclass)
    methods = info.get("methods", {}) if info else {}
    if not methods:
        return None
    if "anything" in methods:
        return frozenset({ANY})
    kinds = {kind for name, kind in _METHOD_TO_KIND.items() if name in methods}
    return frozenset(kinds) if kinds else None


def inlet_acceptance(maxclass: str, index: int) -> Tuple[FrozenSet[str], bool]:
    """``(accept-set, authoritative)`` for ``maxclass``'s inlet ``index``.

    ``authoritative`` means the set is the inlet's *complete* vocabulary, so a
    message outside it is a definite error. The left inlet's vocabulary is taken
    from the ``<methodlist>`` (real data); a signal-only inlet is authoritative
    by its type; everything else is non-authoritative (conservative / skip).
    """
    override = _INLET_ACCEPTS.get(maxclass, {}).get(index)
    if override is not None:
        return override, True
    info = get_object_info(maxclass)
    inlets = info.get("inlets", []) if info else []
    type_set = (
        _accepts_from_type(inlets[index].get("type", ""))
        if 0 <= index < len(inlets)
        else frozenset({ANY})
    )
    if index == 0:
        from_methods = _accepts_from_methods(maxclass)
        if from_methods is not None:
            if ANY in from_methods:
                return frozenset({ANY}), True
            # union with the type-derived set so a signal/float inlet keeps its
            # signal capability even if the method list omits it
            return frozenset(from_methods | type_set), True
    if type_set == frozenset({SIGNAL}):
        return type_set, True  # signal-only inlets are strict
    return type_set, False


def inlet_accepts(maxclass: str, index: int) -> FrozenSet[str]:
    """Message kinds accepted by ``maxclass``'s inlet ``index`` (``{ANY}`` if unsure)."""
    return inlet_acceptance(maxclass, index)[0]


def inlet_rejects_bang(maxclass: str, index: int) -> bool:
    """True if a bang into this signal inlet is a known error (pure DSP objects)."""
    return index in _SIGNAL_INLET_REJECTS_BANG.get(maxclass, set())


def message_compatible(
    emit: str, accepts: FrozenSet[str], authoritative: bool = False
) -> Optional[bool]:
    """Whether an outlet emitting ``emit`` may connect to an inlet accepting ``accepts``.

    Returns ``True`` (fine), ``False`` (definite error), or ``None`` (ambiguous
    -- skip). When ``authoritative`` is set, ``accepts`` is the inlet's complete
    vocabulary, so a message outside it is a definite error (this is how a bang
    into ``cycle~`` is caught while a bang into ``adsr~`` -- which has an
    ``anything`` method -- is allowed). Otherwise the check stays conservative so
    on-by-default validation never rejects a valid patch.
    """
    if ANY in accepts:
        return True  # inlet takes anything
    if emit == ANY:
        return None  # unknown outlet -- cannot judge
    if emit == SIGNAL:
        # a signal needs a signal-capable inlet; a known non-signal inlet errors
        return SIGNAL in accepts
    # control message (bang / int / float / list)
    if emit in accepts:
        return True
    if emit in (INT, FLOAT) and (INT in accepts or FLOAT in accepts):
        return True  # int/float coerce
    if authoritative:
        return False  # full vocabulary known and it excludes this message
    if accepts == frozenset({SIGNAL}):
        return False  # control message into a signal-only inlet
    return None  # ambiguous -- skip
