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
from typing import Callable, FrozenSet, List, Optional, Tuple

from .aliases import ALIASES
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
    "qmetro": {0: BANG},
    "tempo": {0: INT},  # beat count, not a bang
    "delay": {0: BANG},
    "del": {0: BANG},
    "loadbang": {0: BANG},
    "closebang": {0: BANG},
    "freebang": {0: BANG},
    "button": {0: BANG},  # the bng UI object
    "bangbang": {0: BANG, 1: BANG},
    "uzi": {0: BANG, 1: BANG, 2: INT},
    "line": {1: BANG},  # outlet 0 may ramp a list
    "flonum": {0: FLOAT},
    "number": {0: INT},
    "toggle": {0: INT},
    "random": {0: INT},
    "drunk": {0: INT},
    "urn": {0: INT, 1: BANG},
    "counter": {0: INT},
    "kslider": {0: INT, 1: INT},
    "mtof": {0: FLOAT},
    "timer": {0: FLOAT},
    "pong": {0: FLOAT},  # maxref types it "signal"; its digest says (float)
}

# maxref outlet types that name one control message kind exactly.
_TYPED_EMIT = {
    "bang": BANG,
    "int": INT,
    "long": INT,
    "float": FLOAT,
    "double": FLOAT,
    "int/float": FLOAT,  # int and float coerce
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
    """Positional arguments in a box's ``text``: no name, no ``@attr`` tail.

    A double-quoted argument is one token, as in Max.
    """
    from ..utils import parse_attr_args

    tokens = re.findall(r'"[^"]*"|\S+', text or "")[1:]
    return parse_attr_args(tokens)[0]


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


def _scale_value_in(a: List[str]) -> _Counts:
    n = _first_int(a)
    return (n, None) if n and n > 0 else (None, None)


def _match_counts(a: List[str]) -> _Counts:
    # select/route N: a right inlet per match to reset it; N match outlets + 1
    return (len(a) + 1, len(a) + 1) if a else (None, None)


def _unjoin_counts(a: List[str]) -> _Counts:
    n = _first_int(a)  # unjoin N: N outlets (at least 2) + 1 overflow
    return (None, max(n, 2) + 1) if n and n > 0 else (None, None)


def _matrix_counts(info_outlets: int) -> Callable[[List[str]], _Counts]:
    """``matrix~ A B``: A inlets, B outlets + info outlets (1; 2 for mc.)."""

    def counts(a: List[str]) -> _Counts:
        ints = [int(t) for t in a[:2] if re.fullmatch(r"\d+", t)]
        if not ints:
            return (None, None)
        return (ints[0], ints[1] + info_outlets if len(ints) > 1 else None)

    return counts


def _channel_args_in(a: List[str]) -> _Counts:
    return (len(a), None) if a else (None, None)  # dac~ 1 2 3 4


def _channel_args_out(a: List[str]) -> _Counts:
    return (None, len(a)) if a else (None, None)  # adc~ 1 2 3 4


def _expr_counts(a: List[str]) -> _Counts:
    # expr/vexpr/if: an inlet per highest $i/$f/$s/$x index; if: outN outlets
    s = " ".join(a)
    ins = [int(n) for n in re.findall(r"\$[ifsx](\d+)", s)]
    outs = [int(n) for n in re.findall(r"\bout(\d+)\b", s)]
    return (max(ins) if ins else None, max(outs) if outs else None)


def _sprintf_counts(a: List[str]) -> _Counts:
    n = len(re.findall(r"%[-+ #0-9.]*[a-zA-Z]", " ".join(a).replace("%%", "")))
    return (n, None) if n > 1 else (None, None)


def _unpack_counts(a: List[str]) -> _Counts:
    return (None, len(a)) if a else (None, None)


def _pack_counts(a: List[str]) -> _Counts:
    return (len(a), None) if a else (None, None)


_ARG_RESOLVERS = {
    "limi~": _scale_value_both,
    "matrix~": _matrix_counts(1),
    "mc.matrix~": _matrix_counts(2),
    "mc.pack~": _scale_value_in,
    "mc.unpack~": _scale_value_out,
    "mc.combine~": _scale_value_in,
    "gate": _scale_value_out,
    "selector~": _selector_counts,
    "mc.selector~": _selector_counts,
    "switch": _switch_counts,
    "select": _match_counts,
    "route": _match_counts,
    "routepass": _match_counts,
    "unpack": _unpack_counts,
    "pack": _pack_counts,
    "pak": _pack_counts,
    "combine": _pack_counts,
    "join": _scale_value_in,
    "unjoin": _unjoin_counts,
    "funnel": _scale_value_in,
    "spray": _scale_value_out,
    "bangbang": _scale_value_out,
    "jit.gl.multiple": _scale_value_in,
    "dac~": _channel_args_in,
    "adc~": _channel_args_out,
    "expr": _expr_counts,
    "vexpr": _expr_counts,
    "if": _expr_counts,
    "sprintf": _sprintf_counts,
    "trigger": _unpack_counts,  # one outlet per argument
}

# Objects whose maxref entry omits a port list. Counts are those Max writes.
_PORT_COUNTS: dict[str, _Counts] = {
    "midiformat": (7, 2),
    "adstatus": (2, 2),
    "funnel": (2, 1),
    "if": (1, 1),
    "dict.view": (1, None),
    "udpsend": (1, 0),
    "onecopy": (1, 0),
}

# Objects whose port counts follow their content or attributes (a script, a
# loaded patcher, ``@chans``), which neither maxref nor the text gives. Their
# counts are unknown, so range checks skip them. ``mc.*`` objects are included
# by prefix: 13 of the 17 seen in Max-written patches outnumber maxref.
_VARIABLE_IO = frozenset(
    {
        "js",
        "jsui",
        "gen",
        "gen~",
        "jit.gen",
        "jit.pix",
        "jit.gl.pix",
        "poly~",
        "pvar",
        "pipe",
        "sfplay~",
        "groove~",
        "record~",
        "wave~",
        "jit.glue",
        "jit.scissors",
        "sxformat",
        "dict.pack",
    }
)


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
    return _TYPED_EMIT.get(t, ANY)  # other control outlets: unknown unless curated


# --- public API ------------------------------------------------------------
def port_counts(
    maxclass: str, text: Optional[str] = None
) -> tuple[Optional[int], Optional[int]]:
    """Return ``(inlet_count, outlet_count)`` for an object, arg-aware.

    Uses the leading integer argument for objects whose I/O scales with it
    (``limi~ 2`` -> 2 in / 2 out), otherwise the maxref default. ``None`` for a
    dimension means "unknown" (skip range checks).
    """
    if maxclass in _PORT_COUNTS:
        n_in, n_out = _PORT_COUNTS[maxclass]
    elif maxclass in _VARIABLE_IO or maxclass.startswith("mc."):
        n_in = n_out = None
    else:
        info = get_object_info(maxclass)
        # an empty inlet list means maxref omits it: 0-inlet objects are rare
        n_in = (len(info["inlets"]) or None) if info and "inlets" in info else None
        n_out = len(info["outlets"]) if info and "outlets" in info else None
    r_in, r_out = arg_port_counts(maxclass, text)
    return (
        r_in if r_in is not None else n_in,
        r_out if r_out is not None else n_out,
    )


def arg_port_counts(maxclass: str, text: Optional[str] = None) -> _Counts:
    """``(inlet_count, outlet_count)`` implied by ``text``'s arguments alone.

    ``None`` for a dimension that does not depend on arguments.
    """
    resolver = _ARG_RESOLVERS.get(maxclass) or _ARG_RESOLVERS.get(
        ALIASES.get(maxclass, "")
    )
    return resolver(_args(text)) if resolver is not None else (None, None)


def subpatcher_counts(box: object) -> _Counts:
    """Port counts for a subpatcher/bpatcher box, from its nested patcher.

    A subpatcher's real inlet/outlet count is the number of ``inlet`` / ``outlet``
    objects it contains, not the maxref default. Returns ``(None, None)`` for a
    box with no nested patcher.
    """
    child = getattr(box, "_patcher", None)
    if child is None or getattr(child, "classnamespace", "box") != "box":
        return (None, None)  # rnbo~ and gen~ ports come from in/out objects
    from ..utils import object_name

    boxes = getattr(child, "_boxes", [])
    n_in = sum(1 for b in boxes if object_name(b) == "inlet")
    n_out = sum(1 for b in boxes if object_name(b) == "outlet")
    return (n_in, n_out)


# Objects whose ports come from their code or the patch they load, so the box's
# declared numinlets/numoutlets are the only source of counts.
DYNAMIC_IO_MAXCLASSES = frozenset({"gen.codebox~", "codebox", "codebox~", "bpatcher"})


def _widen(ref: Optional[int], declared: object) -> Optional[int]:
    if ref is None or not isinstance(declared, int):
        return ref
    return max(ref, declared)


def box_port_counts(box: object, name: str) -> _Counts:
    """``(inlet_count, outlet_count)`` for a box, for range checks.

    Order: a subpatcher's content, then a dynamic box's declared counts, then
    :func:`port_counts`. Declared counts widen the last but never narrow it: a
    box loaded from a file carries the counts Max wrote, which are exact.
    """
    sub = subpatcher_counts(box)
    if sub != (None, None):
        return sub
    n_in, n_out = getattr(box, "numinlets", None), getattr(box, "numoutlets", None)
    if getattr(box, "maxclass", None) in DYNAMIC_IO_MAXCLASSES:
        return (n_in, n_out)
    ref_in, ref_out = port_counts(name, getattr(box, "text", None))
    return (_widen(ref_in, n_in), _widen(ref_out, n_out))


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


# A right inlet is strict only when its digest describes a signal and nothing
# else: "(signal) Trigger", not "(signal/float) Duty Cycle" or "Reset Input".
_PLAIN_SIGNAL_DIGEST = re.compile(r"\s*\(signal\)[^,;]*", re.IGNORECASE)
_CONTROL_WORD = re.compile(r"\b(int|float|number|bang|list|reset|message)s?\b", re.I)

_OTHER_INLET = re.compile(
    r"\b(right|middle|other|either|each|any|all|second|third)\b[^.]*\binlets?\b"
)


def _left_inlet_only(spec: object) -> bool:
    """True if a maxref method's description confines it to the left inlet."""
    text = str(spec.get("description", "") if isinstance(spec, dict) else "").lower()
    return "left inlet" in text and not _OTHER_INLET.search(text)


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
            # signal capability even if the method list omits it; a placeholder
            # type (INLET_TYPE -> ANY) adds nothing
            return frozenset(from_methods | (type_set - {ANY})), True
    if type_set == frozenset({SIGNAL}):
        # maxref types many right inlets "signal" that also take numbers
        # (clip~ min/max, scope~ buffer size); its methods give that away
        methods = {
            name
            for name, spec in (info.get("methods", {}) if info else {}).items()
            if not _left_inlet_only(spec)
        }
        if "anything" in methods:
            return frozenset({ANY}), False
        control = {
            _METHOD_TO_KIND[m] for m in methods & {"bang", "int", "float", "list"}
        }
        if control:
            return frozenset({SIGNAL} | control), False
        digest = inlets[index].get("digest", "") if 0 <= index < len(inlets) else ""
        if not _PLAIN_SIGNAL_DIGEST.fullmatch(digest) or _CONTROL_WORD.search(digest):
            return frozenset({ANY}), False  # digest says more than "signal"
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
