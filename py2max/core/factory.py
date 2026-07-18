"""BoxFactory mixin for the Patcher class.

Holds the object-creation methods (``add_box``, ``add_line``, the
``add_<type>`` factory methods, and their helpers) extracted from ``Patcher``
to keep that class focused on the object graph and layout. Mixed into
``Patcher`` via inheritance, so these remain ordinary ``Patcher`` methods with
no API change -- adding a new object type means editing this file, not the
core class.
"""

import re
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

from py2max import maxref

from ..exceptions import InvalidConnectionError
from ..log import get_logger
from .abstract import AbstractBox, AbstractPatcher, AbstractPatchline
from .box import Box
from .common import Rect
from .patchline import Patchline

if TYPE_CHECKING:
    from .patcher import Patcher

logger = get_logger(__name__)

# Max objects whose inlet/outlet counts are determined by their code rather
# than by a fixed maxref entry. Connection validation for these consults the
# box's own declared numinlets/numoutlets instead of the static maxref data.
DYNAMIC_IO_MAXCLASSES = frozenset({"gen.codebox~", "codebox", "codebox~"})


def _max_gen_io_index(code: str, kind: str) -> int:
    """Highest ``in<N>`` / ``out<N>`` index referenced in gen ``code``.

    gen codeboxes derive their inlet/outlet count from the code: ``in1``,
    ``in2``, ... and ``out1``, ``out2``, .... Returns at least 1 since a gen
    codebox always has one signal inlet and one signal outlet.
    """
    indices = [int(m) for m in re.findall(rf"\b{kind}(\d+)\b", code)]
    return max([1, *indices])


# Box attributes valid on (nearly) every Max object, independent of an object's
# own maxref attribute set. Used by add_box when validate_attrs is enabled to
# whitelist universal/jbox attributes plus the structural keys py2max emits, so
# only genuinely unknown keys (typically typos) are flagged.
UNIVERSAL_BOX_ATTRS = frozenset(
    {
        # structural keys py2max sets on boxes
        "text",
        "maxclass",
        "numinlets",
        "numoutlets",
        "outlettype",
        "id",
        "patching_rect",
        "presentation_rect",
        "presentation",
        "code",
        "data",
        "table_data",
        "editor_rect",
        "embed",
        "hint",
        "minimum",
        "maximum",
        "parameter_enable",
        "saved_attribute_attributes",
        "saved_object_attributes",
        # common universal jbox attributes
        "varname",
        "prototypename",
        "hidden",
        "ignoreclick",
        "bgcolor",
        "bgfillcolor",
        "bordercolor",
        "textcolor",
        "color",
        "elementcolor",
        "accentcolor",
        "fontname",
        "fontsize",
        "fontface",
        "annotation",
        "annotation_name",
        "rounded",
        "border",
        "style",
        "comment",
    }
)


class BoxFactoryMixin(AbstractPatcher):
    """Object creation (boxes, patchlines, and the add_* factory) for Patcher."""

    def _validate_box_attrs(self, box: "Box") -> None:
        """Warn when a box carries keywords that are not known attributes.

        Best-effort lint, enabled by ``Patcher(validate_attrs=True)``. The known
        set is the object's maxref attributes plus ``UNIVERSAL_BOX_ATTRS``;
        objects with no maxref entry are skipped (cannot be checked).
        """
        name = self._get_object_name(box)
        info = maxref.get_object_info(name)
        if not info:
            return
        known = UNIVERSAL_BOX_ATTRS | set(info.get("attributes", {}).keys())
        for key in box._kwds:
            if key not in known:
                warnings.warn(
                    f"Unknown attribute {key!r} for Max object {name!r} "
                    f"(possible typo?)",
                    UserWarning,
                    stacklevel=3,
                )

    def _get_object_name(self, obj: AbstractBox) -> str:
        """Get the actual object name for validation purposes.

        See ``utils.object_name``. Uses the box ``text`` property so it resolves
        correctly for both programmatic and file-loaded boxes.
        """
        from ..utils import object_name

        return object_name(obj)

    def add_box(
        self,
        box: "Box",
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
    ) -> "Box":
        """registers the box and adds it to the patcher"""

        assert box.id, f"object {box} must have an id"
        if self._validate_attrs:
            self._validate_box_attrs(box)
        self._node_ids.append(box.id)
        self._objects[box.id] = box
        self._boxes.append(box)
        if comment:
            self.add_associated_comment(box, comment, comment_pos)
        return box

    def add_associated_comment(
        self, box: "Box", comment: str, comment_pos: Optional[str] = None
    ) -> None:
        """Store a comment association to be processed later during layout optimization or save.

        This defers the actual comment positioning until after layout optimization,
        ensuring comments stay properly positioned relative to their associated boxes.
        """

        if comment_pos:
            assert comment_pos in [
                "above",
                "below",
                "right",
                "left",
            ], f"comment:{comment} / comment_pos: {comment_pos}"

        # Store the association for deferred processing
        if box.id is None:
            raise AssertionError("associated comment requires box with id")
        self._pending_comments.append((box.id, comment, comment_pos))

    def _process_pending_comments(self) -> None:
        """Process all pending comment associations and position comments relative to their boxes.

        This method is called during layout optimization and save operations to ensure
        comments are positioned correctly after any layout changes.
        """
        for box_id, comment_text, comment_pos in self._pending_comments:
            if box_id not in self._objects:
                continue  # Skip if box was removed

            box = self._objects[box_id]
            rect = box.patching_rect
            x, y, w, h = rect

            # Adjust rect height if needed
            if h != self._layout_mgr.box_height:
                if box.maxclass in maxref.MAXCLASS_DEFAULTS:
                    dh: float = 0.0
                    _, _, _, dh = maxref.MAXCLASS_DEFAULTS[box.maxclass][
                        "patching_rect"
                    ]
                    rect = Rect(x, y, w, dh)
                else:
                    h = self._layout_mgr.box_height
                    rect = Rect(x, y, w, h)

            # Calculate comment position
            if comment_pos:
                patching_rect = getattr(self._layout_mgr, comment_pos)(rect)
            else:
                patching_rect = self._layout_mgr.above(rect)

            # Create the comment with appropriate justification
            if comment_pos == "left":  # special case
                self.add_comment(comment_text, patching_rect, justify="right")
            else:
                self.add_comment(comment_text, patching_rect)

        # Clear pending comments after processing
        self._pending_comments.clear()

    def add_patchline_by_index(
        self, src_id: str, dst_id: str, dst_inlet: int = 0, src_outlet: int = 0
    ) -> "Patchline":
        """Patchline creation between two objects using stored indexes"""

        src = self._objects[src_id]
        dst = self._objects[dst_id]
        assert src.id and dst.id, f"object {src} and {dst} require ids"
        return self.add_patchline(src.id, src_outlet, dst.id, dst_inlet)

    def add_patchline(
        self, src_id: str, src_outlet: int, dst_id: str, dst_inlet: int
    ) -> "Patchline":
        """Primary patchline creation method with validation and logging.

        Args:
            src_id: Source object ID.
            src_outlet: Source outlet index.
            dst_id: Destination object ID.
            dst_inlet: Destination inlet index.

        Returns:
            Created Patchline object.

        Raises:
            InvalidConnectionError: If connection validation fails.
        """
        logger.debug(
            f"Adding patchline: {src_id}[{src_outlet}] -> {dst_id}[{dst_inlet}]"
        )

        # Validate connection if validation is enabled
        if self._validate_connections:
            src_obj = self._objects.get(src_id)
            dst_obj = self._objects.get(dst_id)

            if not src_obj:
                raise InvalidConnectionError(
                    f"Source object not found: {src_id}",
                    src=src_id,
                    dst=dst_id,
                    outlet=src_outlet,
                    inlet=dst_inlet,
                )

            if not dst_obj:
                raise InvalidConnectionError(
                    f"Destination object not found: {dst_id}",
                    src=src_id,
                    dst=dst_id,
                    outlet=src_outlet,
                    inlet=dst_inlet,
                )

            # Get the actual object names for validation
            src_name = self._get_object_name(src_obj)
            dst_name = self._get_object_name(dst_obj)

            src_dynamic = src_obj.maxclass in DYNAMIC_IO_MAXCLASSES
            dst_dynamic = dst_obj.maxclass in DYNAMIC_IO_MAXCLASSES

            if src_dynamic or dst_dynamic:
                # Codeboxes derive their inlet/outlet counts from their code,
                # so bound-check indices against the box's own declared counts
                # rather than the fixed maxref entry. Type checking is skipped
                # because codebox I/O is always signal.
                src_outlets = (
                    src_obj.numoutlets
                    if src_dynamic
                    else maxref.get_outlet_count(src_name)
                )
                dst_inlets = (
                    dst_obj.numinlets
                    if dst_dynamic
                    else maxref.get_inlet_count(dst_name)
                )
                error_msg = ""
                if src_outlets is not None and src_outlet >= src_outlets:
                    error_msg = (
                        f"Object '{src_name}' only has {src_outlets} outlet(s), "
                        f"cannot connect from outlet {src_outlet}"
                    )
                elif dst_inlets is not None and dst_inlet >= dst_inlets:
                    error_msg = (
                        f"Object '{dst_name}' only has {dst_inlets} inlet(s), "
                        f"cannot connect to inlet {dst_inlet}"
                    )
                is_valid = not error_msg
            else:
                is_valid, error_msg = maxref.validate_connection(
                    src_name, src_outlet, dst_name, dst_inlet
                )

            if not is_valid:
                logger.warning(
                    f"Connection validation failed: {src_name}[{src_outlet}] -> {dst_name}[{dst_inlet}]: {error_msg}"
                )
                raise InvalidConnectionError(
                    f"Invalid connection from {src_name}[{src_outlet}] to {dst_name}[{dst_inlet}]: {error_msg}",
                    src=src_id,
                    dst=dst_id,
                    outlet=src_outlet,
                    inlet=dst_inlet,
                )

        # Order of lines between the same pair of objects: Max uses it to fan
        # parallel wires apart. Derive it from the connections that currently
        # exist for this (src, dst) pair rather than a single-slot memo of the
        # last link -- the memo reset ``order`` to 0 whenever any other
        # connection intervened, collapsing parallel wires (and it also could
        # not account for lines restored from a loaded patch).
        order = sum(1 for pl in self._lines if pl.src == src_id and pl.dst == dst_id)
        src, dst = [src_id, src_outlet], [dst_id, dst_inlet]
        patchline = Patchline(source=src, destination=dst, order=order)
        self._lines.append(patchline)
        self._edge_ids.append((src_id, dst_id))

        logger.debug(
            f"Created patchline (order={order}): {src_id}[{src_outlet}] -> {dst_id}[{dst_inlet}]"
        )
        return patchline

    def add_line(
        self, src_obj: "Box", dst_obj: "Box", inlet: int = 0, outlet: int = 0
    ) -> "Patchline":
        """Create a connection between two objects.

        Connects an outlet of the source object to an inlet of the destination
        object. Validates the connection if validation is enabled.

        Args:
            src_obj: Source object to connect from.
            dst_obj: Destination object to connect to.
            inlet: Destination inlet index (default: 0).
            outlet: Source outlet index (default: 0).

        Returns:
            The created Patchline object.

        Raises:
            InvalidConnectionError: If connection validation fails.

        Example:
            >>> osc = p.add_textbox('cycle~ 440')
            >>> gain = p.add_textbox('gain~')
            >>> p.add_line(osc, gain)  # Connect outlet 0 to inlet 0
        """
        assert src_obj.id and dst_obj.id, f"objects {src_obj} and {dst_obj} require ids"
        return self.add_patchline(src_obj.id, outlet, dst_obj.id, inlet)

    # alias for add_line
    link = add_line

    def add_textbox(
        self,
        text: str,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[List[str]] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a text-based Max object to the patch.

        Creates a Max object from a text specification (e.g., 'cycle~ 440').
        Automatically looks up default attributes and applies appropriate
        maxclass based on the object type.

        Args:
            text: Max object specification (e.g., 'cycle~ 440', 'gain~').
            maxclass: Override the automatically determined maxclass.
            numinlets: Number of input connections.
            numoutlets: Number of output connections.
            outlettype: Types of outputs (e.g., ['signal', 'int']).
            patching_rect: Position and size rectangle.
            id: Unique identifier for the object.
            comment: Optional comment text.
            comment_pos: Comment position ('above', 'below', etc.).
            **kwds: Additional Max object properties.

        Returns:
            The created Box object.

        Example:
            >>> osc = p.add_textbox('cycle~ 440')
            >>> gain = p.add_textbox('gain~')
            >>> metro = p.add_textbox('metro 500')
        """
        _maxclass, *tail = text.split()

        defaults = maxref.MAXCLASS_DEFAULTS.get(_maxclass)

        if defaults:
            if maxclass is None and defaults.get("maxclass"):
                maxclass = defaults["maxclass"]

            if numinlets is None and "numinlets" in defaults:
                numinlets = defaults["numinlets"]

            if numoutlets is None and "numoutlets" in defaults:
                numoutlets = defaults["numoutlets"]

            if outlettype is None and "outlettype" in defaults:
                outlettype = defaults["outlettype"]

        kwds = self._textbox_helper(_maxclass, kwds)

        layout_rect = self.get_pos(maxclass) if maxclass else self.get_pos()
        if patching_rect is None and defaults and defaults.get("patching_rect"):
            default_rect = defaults["patching_rect"]
            patching_rect = Rect(
                layout_rect.x, layout_rect.y, default_rect.w, default_rect.h
            )
        elif patching_rect is None:
            patching_rect = layout_rect

        return self.add_box(
            Box(
                id=id or self.get_id(_maxclass),
                text=text,
                maxclass=maxclass or "newobj",
                numinlets=numinlets if numinlets is not None else 1,
                # An object with no maxref entry gets one outlet by default (not
                # zero): a zero-outlet object cannot act as a connection source,
                # which is wrong for the hand-typed long-tail objects that land
                # here. Matches Box.__init__'s default.
                numoutlets=numoutlets if numoutlets is not None else 1,
                outlettype=outlettype if outlettype is not None else [""],
                patching_rect=patching_rect,
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def _textbox_helper(self, maxclass: str, kwds: Dict[str, Any]) -> Dict[str, Any]:
        """adds special case support for textbox"""
        if self.classnamespace == "rnbo":
            kwds["rnbo_classname"] = maxclass
            if maxclass in ["codebox", "codebox~"]:
                if "code" in kwds and "rnbo_extra_attributes" not in kwds:
                    if "\r" not in kwds["code"]:
                        kwds["code"] = kwds["code"].replace("\n", "\r\n")
                    kwds["rnbo_extra_attributes"] = dict(
                        code=kwds["code"],
                        hot=0,
                    )
        return kwds

    def _add_float(self, value: float, *args: Any, **kwds: Any) -> "Box":
        """type-handler for float values in `add`"""

        assert isinstance(value, float)
        name = None
        if args:
            name = args[0]
        elif "name" in kwds:
            name = kwds.get("name")
        else:
            return self.add_floatparam(longname="", initial=value, **kwds)

        if isinstance(name, str):
            return self.add_floatparam(longname=name, initial=value, **kwds)
        raise ValueError(
            "should be: .add(<float>, '<name>') OR .add(<float>, name='<name>')"
        )

    def _add_int(self, value: int, *args: Any, **kwds: Any) -> "Box":
        """type-handler for int values in `add`"""

        assert isinstance(value, int)
        name = None
        if args:
            name = args[0]
        elif "name" in kwds:
            name = kwds.get("name")
        else:
            return self.add_intparam(longname="", initial=value, **kwds)

        if isinstance(name, str):
            return self.add_intparam(longname=name, initial=value, **kwds)
        raise ValueError(
            "should be: .add(<int>, '<name>') OR .add(<int>, name='<name>')"
        )

    def _add_str(self, value: str, *args: Any, **kwds: Any) -> "Box":
        """type-handler for str values in `add`"""

        assert isinstance(value, str)

        maxclass, *text = value.split()
        txt = " ".join(text)

        # first check _maxclass_methods
        # these methods don't need the maxclass, just the `text` tail of value
        if maxclass in self._maxclass_methods:
            return cast("Box", self._maxclass_methods[maxclass](txt, **kwds))
        # next two require value as a whole
        if maxclass == "p":
            return self.add_subpatcher(value, **kwds)
        if maxclass == "gen~":
            return self.add_gen_tilde(**kwds)
        if maxclass == "gen.codebox~":
            # Tail is the gen code. value.split() collapses whitespace, so this
            # shortcut suits single-line/`;`-terminated code; for multi-line
            # source pass it to add_gen_codebox() directly.
            return self.add_gen_codebox(txt, **kwds)
        if maxclass == "rnbo~":
            return self.add_rnbo(value, **kwds)
        return self.add_textbox(text=value, **kwds)

    def add(self, value: Any, *args: Any, **kwds: Any) -> "Box":
        """generic adder: value can be a number or a list or text for an object."""

        if isinstance(value, float):
            return self._add_float(value, *args, **kwds)

        if isinstance(value, int):
            return self._add_int(value, *args, **kwds)

        if isinstance(value, str):
            return self._add_str(value, *args, **kwds)

        raise NotImplementedError

    def add_codebox(
        self,
        code: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        tilde: bool = False,
        **kwds: Any,
    ) -> "Box":
        """Add a codebox."""

        _maxclass = "codebox~" if tilde else "codebox"
        if "\r" not in code:
            code = code.replace("\n", "\r\n")

        if self.classnamespace == "rnbo":
            kwds["rnbo_classname"] = _maxclass
            if "rnbo_extra_attributes" not in kwds:
                kwds["rnbo_extra_attributes"] = dict(
                    code=code,
                    hot=0,
                )

        return self.add_box(
            Box(
                id=id or self.get_id(_maxclass),
                code=code,
                maxclass=_maxclass,
                outlettype=[""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_codebox_tilde(
        self,
        code: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a codebox_tilde"""
        return self.add_codebox(
            code, patching_rect, id, comment, comment_pos, tilde=True, **kwds
        )

    def add_gen_codebox(
        self,
        code: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[List[str]] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a standalone ``gen.codebox~`` object.

        Unlike :meth:`add_codebox` (which emits the ``codebox~`` object meant to
        live *inside* a ``gen~`` or ``rnbo~`` subpatcher), this creates the
        self-contained ``gen.codebox~`` object that lives directly in a regular
        Max patcher -- a complete gen patch in a single box, with no subpatcher
        wrapper. This is the form emitted by gen transpilers.

        A gen codebox's inlet/outlet counts are dynamic: they are determined by
        the highest ``inN`` / ``outN`` references in the code. They are derived
        automatically when ``numinlets`` / ``numoutlets`` are not given (each
        defaults to at least 1).
        """
        if "\r" not in code:
            code = code.replace("\n", "\r\n")

        if numinlets is None:
            numinlets = _max_gen_io_index(code, "in")
        if numoutlets is None:
            numoutlets = _max_gen_io_index(code, "out")

        kwds.setdefault("fontname", "<Monospaced>")
        kwds.setdefault("fontsize", 12.0)

        return self.add_box(
            Box(
                id=id or self.get_id("gen.codebox~"),
                code=code,
                maxclass="gen.codebox~",
                numinlets=numinlets,
                numoutlets=numoutlets,
                outlettype=outlettype or ["signal"] * numoutlets,
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_message(
        self,
        text: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a max message."""

        return self.add_box(
            Box(
                id=id or self.get_id("message"),
                text=text or "",
                maxclass="message",
                numinlets=2,
                numoutlets=1,
                outlettype=[""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_comment(
        self,
        text: str,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        justify: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a basic comment object."""
        if justify:
            kwds["textjustification"] = {"left": 0, "center": 1, "right": 2}[justify]
        return self.add_box(
            Box(
                id=id or self.get_id("comment"),
                text=text,
                maxclass="comment",
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            )
        )

    def add_intbox(
        self,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add an int box object."""

        return self.add_box(
            Box(
                id=id or self.get_id("number"),
                maxclass="number",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    # alias
    add_int = add_intbox

    def add_floatbox(
        self,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add an float box object."""

        return self.add_box(
            Box(
                id=id or self.get_id("flonum"),
                maxclass="flonum",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    # alias
    add_float = add_floatbox

    def add_floatparam(
        self,
        longname: str,
        initial: Optional[float] = None,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        shortname: Optional[str] = None,
        id: Optional[str] = None,
        rect: Optional[Rect] = None,
        hint: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a float parameter object."""

        return self.add_box(
            Box(
                id=id or self.get_id("flonum"),
                maxclass="flonum",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                parameter_enable=1,
                saved_attribute_attributes=dict(
                    valueof=dict(
                        parameter_initial=[initial or 0.5],
                        parameter_initial_enable=1,
                        parameter_longname=longname,
                        # parameter_mmax=maximum,
                        parameter_shortname=shortname or "",
                        parameter_type=0,
                    )
                ),
                maximum=maximum,
                minimum=minimum,
                patching_rect=rect or self.get_pos(),
                hint=hint or (longname if self._auto_hints else ""),
                **kwds,
            ),
            comment or longname,  # units can also be added here
            comment_pos,
        )

    def add_intparam(
        self,
        longname: str,
        initial: Optional[int] = None,
        minimum: Optional[int] = None,
        maximum: Optional[int] = None,
        shortname: Optional[str] = None,
        id: Optional[str] = None,
        rect: Optional[Rect] = None,
        hint: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add an int parameter object."""

        return self.add_box(
            Box(
                id=id or self.get_id("number"),
                maxclass="number",
                numinlets=1,
                numoutlets=2,
                outlettype=["", "bang"],
                parameter_enable=1,
                saved_attribute_attributes=dict(
                    valueof=dict(
                        parameter_initial=[initial or 1],
                        parameter_initial_enable=1,
                        parameter_longname=longname,
                        parameter_mmax=maximum,
                        parameter_shortname=shortname or "",
                        parameter_type=1,
                    )
                ),
                maximum=maximum,
                minimum=minimum,
                patching_rect=rect or self.get_pos(),
                hint=hint or (longname if self._auto_hints else ""),
                **kwds,
            ),
            comment or longname,  # units can also be added here
            comment_pos,
        )

    # -- Preset / parameter scaffolding --------------------------------------

    def add_pattrstorage(self, name: str = "presets", **kwds: Any) -> "Box":
        """Add a ``pattrstorage`` object for saving and recalling named presets.

        ``pattrstorage`` stores presets of every parameter-enabled and
        pattr-bound object in the patcher. Pair it with :meth:`add_autopattr`
        (or use :meth:`add_preset_system`) so named objects are exposed
        automatically.

        Args:
            name: the storage name (the pattrstorage argument).
            **kwds: extra attributes forwarded to the box.
        """
        return self.add_textbox(
            f"pattrstorage {name}".strip(),
            numinlets=1,
            numoutlets=1,
            outlettype=[""],
            saved_object_attributes=dict(
                client_rect=[0, 0, 0, 0],
                parameter_enable=0,
                parameter_mappable=0,
            ),
            **kwds,
        )

    def add_autopattr(self, **kwds: Any) -> "Box":
        """Add an ``autopattr`` object exposing named objects to the pattr system.

        Any object with a scripting name (``varname``) is bound automatically,
        so it participates in ``pattrstorage`` presets without a per-object
        ``pattr``.
        """
        return self.add_textbox(
            "autopattr",
            numinlets=1,
            numoutlets=4,
            outlettype=["", "", "", ""],
            **kwds,
        )

    def add_preset_system(
        self, name: str = "presets", **kwds: Any
    ) -> Tuple["Box", "Box"]:
        """Add a standard preset system: ``autopattr`` + ``pattrstorage``, wired.

        Connects ``autopattr`` to ``pattrstorage`` so that any object with a
        scripting name (``varname``) or ``parameter_enable=1`` participates in
        presets. Returns ``(autopattr_box, pattrstorage_box)``.
        """
        autopattr = self.add_autopattr()
        storage = self.add_pattrstorage(name, **kwds)
        self.add_line(autopattr, storage)
        return autopattr, storage

    def enable_parameter(
        self,
        box: "Box",
        longname: str,
        shortname: str = "",
        ptype: int = 0,
        initial: Optional[float] = None,
    ) -> "Box":
        """Mark an existing box as a Max parameter.

        Parameterized objects participate in ``pattrstorage`` presets and, in a
        Max for Live device, appear as automatable parameters. Use this to turn
        a plain UI object (toggle, dial, slider, ...) into a parameter without
        rebuilding it.

        Args:
            box: the box to parameterize.
            longname: parameter long name (its preset/automation name).
            shortname: optional short name.
            ptype: parameter type (0=float, 1=int, 2=enum, 3=blob).
            initial: optional initial value.

        Returns:
            The same box, for chaining.
        """
        box._kwds["parameter_enable"] = 1
        valueof: Dict[str, Any] = dict(
            parameter_longname=longname,
            parameter_shortname=shortname,
            parameter_type=ptype,
        )
        if initial is not None:
            valueof["parameter_initial"] = [initial]
            valueof["parameter_initial_enable"] = 1
        box._kwds["saved_attribute_attributes"] = dict(valueof=valueof)
        return box

    def add_attr(
        self,
        name: str,
        value: float,
        shortname: Optional[str] = None,
        id: Optional[str] = None,
        rect: Optional[Rect] = None,
        hint: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        autovar: bool = True,
        show_label: bool = False,
        **kwds: Any,
    ) -> "Box":
        """create a param-linke attrui entry"""
        if autovar:
            kwds["varname"] = name

        return self.add_box(
            Box(
                id=id or self.get_id("attrui"),
                text="attrui",
                maxclass="attrui",
                attr=name,
                parameter_enable=1,
                attr_display=show_label,
                saved_attribute_attributes=dict(
                    valueof=dict(
                        parameter_initial=[name, value],
                        parameter_initial_enable=1,
                        parameter_longname=name,
                        parameter_shortname=shortname or "",
                    )
                ),
                patching_rect=rect or self.get_pos(),
                hint=name if self._auto_hints else hint or "",
                **kwds,
            ),
            comment or name,  # units can also be added here
            comment_pos,
        )

    def add_subpatcher(
        self,
        text: str,
        maxclass: Optional[str] = None,
        numinlets: Optional[int] = None,
        numoutlets: Optional[int] = None,
        outlettype: Optional[List[str]] = None,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        patcher: Optional["Patcher"] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a subpatcher object."""
        from .patcher import Patcher

        # For subpatchers, use the text (e.g., "p subpatch") for semantic ID
        obj_name = text.split()[0] if text else "newobj"
        return self.add_box(
            Box(
                id=id or self.get_id(obj_name),
                text=text,
                maxclass=maxclass or "newobj",
                numinlets=numinlets or 1,
                numoutlets=numoutlets or 0,
                outlettype=outlettype or [""],
                patching_rect=patching_rect or self.get_pos(),
                patcher=patcher or Patcher(parent=self),
                **kwds,
            )
        )

    def _drop_line(self, line: AbstractPatchline) -> None:
        """Remove a patchline (and its edge id) from this patcher."""
        if line in self._lines:
            self._lines.remove(line)
        edge = (line.src, line.dst)
        if edge in self._edge_ids:
            self._edge_ids.remove(edge)

    @staticmethod
    def _as_box_id(box: "Union[Box, str]") -> str:
        """Resolve a Box or id string to its id."""
        return box.id if isinstance(box, Box) else box  # type: ignore[return-value]

    def remove_line(self, line: "Patchline") -> None:
        """Remove a specific patchline connection from the patcher."""
        self._drop_line(line)

    def disconnect(
        self,
        src: "Union[Box, str]",
        dst: "Union[Box, str]",
        outlet: int = 0,
        inlet: int = 0,
    ) -> int:
        """Remove connection(s) between ``src`` and ``dst``.

        Removes every patchline from ``src[outlet]`` to ``dst[inlet]`` and
        returns how many were removed (0 if none matched). ``src``/``dst`` may be
        Box objects or their ids.

        Example:
            >>> p.add_line(osc, gain)
            >>> p.disconnect(osc, gain)
            1
        """
        src_id = self._as_box_id(src)
        dst_id = self._as_box_id(dst)
        matches = [
            cast(Patchline, pl)
            for pl in self._lines
            if pl.src == src_id
            and pl.dst == dst_id
            and cast(Patchline, pl).source[1] == outlet
            and cast(Patchline, pl).destination[1] == inlet
        ]
        for line in matches:
            self._drop_line(line)
        return len(matches)

    def remove_box(self, box: "Union[Box, str]") -> Optional["Box"]:
        """Remove a box and every patchline connected to it.

        Accepts a Box or its id. Drops all incident patchlines, the box's entry
        in the object map / node index, and any pending associated comment for
        it. Returns the removed Box, or None if it was not present.

        Example:
            >>> osc = p.add_textbox('cycle~ 440')
            >>> p.remove_box(osc)
        """
        box_id = self._as_box_id(box)

        for line in [pl for pl in self._lines if pl.src == box_id or pl.dst == box_id]:
            self._drop_line(line)

        removed = self._objects.pop(box_id, None)
        target = box if isinstance(box, Box) else removed
        if target in self._boxes:
            self._boxes.remove(target)
        if box_id in self._node_ids:
            self._node_ids.remove(box_id)
        self._pending_comments = [
            pc for pc in self._pending_comments if pc[0] != box_id
        ]
        return cast(Optional["Box"], target)

    # alias for remove_box
    remove = remove_box

    def replace(
        self,
        old: "Union[Box, str]",
        new: "Union[Box, str]",
        **kwds: Any,
    ) -> "Box":
        """Replace a box in place, preserving its position and connections.

        ``old`` (a Box or its id) is swapped for ``new`` -- either the text for a
        replacement object (created with its Max-class defaults) or an
        already-built Box. The replacement takes ``old``'s slot and window
        position, and every patchline incident to ``old`` is rewired to it,
        keeping the same outlet/inlet indices and connection order. Any pending
        associated comment for ``old`` transfers to the replacement. Returns the
        new Box.

        Ports are preserved by index: if the replacement has fewer inlets/outlets
        than the original, wires to the now-missing ports are kept as-is rather
        than silently dropped here (Max drops them on load).

        Example:
            >>> osc = p.add('cycle~ 440')
            >>> p.add_line(osc, gain)
            >>> saw = p.replace(osc, 'saw~ 220')  # saw~ inherits osc's wiring
        """
        old_id = self._as_box_id(old)
        old_box = self._objects.get(old_id)
        if old_box is None:
            raise KeyError(f"cannot replace unknown box {old_id!r}")

        box_idx = self._boxes.index(old_box)
        node_idx = self._node_ids.index(old_id) if old_id in self._node_ids else None
        ox, oy, _, _ = old_box.patching_rect

        # Build the replacement. add_box/add_textbox appends it at the end; it is
        # relocated into old's slot after rewiring. Keep the replacement's own
        # width/height but move it to old's window position.
        if isinstance(new, Box):
            if new.id is None:
                new.id = self.get_id(new.maxclass)
            _, _, nw, nh = new.patching_rect
            new.patching_rect = Rect(ox, oy, nw, nh)
            new_box = self.add_box(new)
        else:
            new_box = self.add_textbox(new, **kwds)
            _, _, nw, nh = new_box.patching_rect
            new_box.patching_rect = Rect(ox, oy, nw, nh)

        new_id = new_box.id
        assert new_id

        # Rewire every incident patchline to the new box, preserving port indices
        # and order, then rebuild the edge index to match.
        for line in self._lines:
            pl = cast(Patchline, line)
            if pl.source and pl.source[0] == old_id:
                pl.source = [new_id, pl.source[1]]
            if pl.destination and pl.destination[0] == old_id:
                pl.destination = [new_id, pl.destination[1]]
        self._edge_ids = [(pl.src, pl.dst) for pl in self._lines]

        # Transfer any pending associated comment from old to new.
        self._pending_comments = [
            (new_id if bid == old_id else bid, text, pos)
            for (bid, text, pos) in self._pending_comments
        ]

        # Drop the old box and move the replacement into its original slot so
        # ordering is preserved (add_* had appended it at the end).
        del self._objects[old_id]
        self._boxes.remove(new_box)  # drop the end-appended copy
        self._boxes[box_idx] = new_box  # overwrite old_box in its slot
        if node_idx is not None:
            self._node_ids.remove(new_id)
            self._node_ids[node_idx] = new_id

        return new_box

    def encapsulate(
        self, boxes: "Iterable[Box]", text: str = "p subpatch", **kwds: Any
    ) -> "Box":
        """Wrap the given boxes into a subpatcher, auto-generating inlet/outlet
        objects for connections that cross the selection boundary.

        - Connections wholly inside the selection move into the subpatcher.
        - Connections crossing in/out are rewired through generated ``inlet`` /
          ``outlet`` objects and the new subpatcher box's ports.
        - Connections wholly outside the selection are left untouched.

        Inlets/outlets are de-duplicated by source port, so multiple wires from
        the same outlet share a single port, matching how patches are usually
        built by hand.

        Args:
            boxes: boxes belonging to this patcher to move into a subpatcher.
            text: the subpatcher box text (e.g. ``"p voice"``).
            **kwds: forwarded to ``add_subpatcher`` (e.g. ``patching_rect``).

        Returns:
            The new subpatcher Box added to this patcher.
        """
        from .patcher import Patcher

        selected = list(boxes)
        id_set = {b.id for b in selected if b.id}
        if not id_set:
            raise ValueError("encapsulate() requires at least one box with an id")

        # Partition existing connections relative to the selection.
        internal: List[Patchline] = []
        incoming: List[Patchline] = []
        outgoing: List[Patchline] = []
        for raw in list(self._lines):
            line = cast(Patchline, raw)
            s_in, d_in = line.src in id_set, line.dst in id_set
            if s_in and d_in:
                internal.append(line)
            elif d_in:
                incoming.append(line)
            elif s_in:
                outgoing.append(line)

        sub = Patcher(parent=self)
        # Avoid id collisions between moved boxes and objects created in the sub.
        moved_oids = [b.oid for b in selected if b.oid is not None]
        if moved_oids:
            sub._id_counter = max(moved_oids)

        # Move the selected boxes into the subpatcher.
        for b in selected:
            if b in self._boxes:
                self._boxes.remove(b)
            if b.id:
                self._objects.pop(b.id, None)
                if b.id in self._node_ids:
                    self._node_ids.remove(b.id)
            child = getattr(b, "_patcher", None)
            if child is not None:
                child._parent = sub
            sub.add_box(b)

        # Move fully-internal connections into the subpatcher.
        for line in internal:
            self._drop_line(line)
            sub._lines.append(line)
            sub._edge_ids.append((line.src, line.dst))

        # Generated connections are correct by construction; skip validation.
        saved = (self._validate_connections, sub._validate_connections)
        self._validate_connections = sub._validate_connections = False
        try:
            # Crossing-in: one inlet per unique external (source_id, outlet).
            inlets: Dict[Tuple[Any, Any], Tuple[int, str]] = {}
            for line in incoming:
                key = (line.source[0], line.source[1])
                if key not in inlets:
                    idx = len(inlets)
                    ibox = sub.add_textbox(
                        "inlet",
                        numinlets=0,
                        numoutlets=1,
                        outlettype=[""],
                        patching_rect=Rect(20.0 + idx * 60, 20.0, 30.0, 30.0),
                    )
                    inlets[key] = (idx, cast(str, ibox.id))
                sub.add_patchline(inlets[key][1], 0, line.dst, int(line.destination[1]))

            # Crossing-out: one outlet per unique internal (source_id, outlet).
            outlets: Dict[Tuple[Any, Any], Tuple[int, str]] = {}
            for line in outgoing:
                key = (line.source[0], line.source[1])
                if key not in outlets:
                    idx = len(outlets)
                    obox = sub.add_textbox(
                        "outlet",
                        numinlets=1,
                        numoutlets=0,
                        outlettype=[],
                        patching_rect=Rect(20.0 + idx * 60, 320.0, 30.0, 30.0),
                    )
                    outlets[key] = (idx, cast(str, obox.id))
                sub.add_patchline(
                    str(line.source[0]), int(line.source[1]), outlets[key][1], 0
                )

            # The crossing lines are now represented inside the sub; drop them.
            for line in incoming + outgoing:
                self._drop_line(line)

            n_in, n_out = len(inlets), len(outlets)
            sub_box = self.add_subpatcher(
                text,
                patcher=sub,
                numinlets=n_in or 1,
                numoutlets=n_out,
                outlettype=[""] * n_out if n_out else None,
                **kwds,
            )
            # add_subpatcher floors inlets at 1; set the exact crossing counts.
            sub_box.numinlets = n_in
            sub_box.numoutlets = n_out
            sub_box_id = cast(str, sub_box.id)

            # Rewire the parent through the new subpatcher box's ports.
            for line in incoming:
                idx = inlets[(line.source[0], line.source[1])][0]
                self.add_patchline(
                    str(line.source[0]), int(line.source[1]), sub_box_id, idx
                )
            for line in outgoing:
                idx = outlets[(line.source[0], line.source[1])][0]
                self.add_patchline(sub_box_id, idx, line.dst, int(line.destination[1]))
        finally:
            self._validate_connections, sub._validate_connections = saved

        return sub_box

    def add_gen(
        self, text: Optional[str] = None, tilde: bool = False, **kwds: Any
    ) -> "Box":
        """Add a gen object."""
        from .patcher import Patcher

        prefix = "gen~" if tilde else "gen"
        _text = f"{prefix} {text}" if text else prefix
        return self.add_subpatcher(
            _text, patcher=Patcher(parent=self, classnamespace="dsp.gen"), **kwds
        )

    def add_gen_tilde(self, text: Optional[str] = None, **kwds: Any) -> "Box":
        """Add a gen~ object."""
        return self.add_gen(text=text, tilde=True, **kwds)

    def add_rnbo(self, text: str = "rnbo~", **kwds: Any) -> "Box":
        """Add an rnbo~ object."""
        from .patcher import Patcher

        if "inletInfo" not in kwds:
            if "numinlets" in kwds:
                inletInfo: Dict[str, List[Any]] = {"IOInfo": []}
                for i in range(kwds["numinlets"]):
                    inletInfo["IOInfo"].append(
                        dict(comment="", index=i + 1, tag=f"in{i + 1}", type="signal")
                    )
                kwds["inletInfo"] = inletInfo
        if "outletInfo" not in kwds:
            if "numoutlets" in kwds:
                outletInfo: Dict[str, List[Any]] = {"IOInfo": []}
                for i in range(kwds["numoutlets"]):
                    outletInfo["IOInfo"].append(
                        dict(comment="", index=i + 1, tag=f"out{i + 1}", type="signal")
                    )
                kwds["outletInfo"] = outletInfo

        return self.add_subpatcher(
            text, patcher=Patcher(parent=self, classnamespace="rnbo"), **kwds
        )

    # -- Multichannel (mc.) / polyphony helpers ------------------------------

    def add_mc(self, text: str, chans: Optional[int] = None, **kwds: Any) -> "Box":
        """Add a multichannel (``mc.``) object.

        Prefixes ``mc.`` to the object name if not already present, and appends
        an ``@chans`` attribute when ``chans`` is given. A single patchline
        between two ``mc.`` objects carries all channels.

        Example:
            >>> p.add_mc("cycle~ 440", chans=4)   # -> "mc.cycle~ 440 @chans 4"
        """
        name = text if text.startswith("mc.") else f"mc.{text}"
        if chans is not None:
            name = f"{name} @chans {chans}"
        return self.add_textbox(name, **kwds)

    def add_poly(self, target: str, voices: int = 1, **kwds: Any) -> "Box":
        """Add a ``poly~`` object hosting ``voices`` instances of ``target``.

        ``target`` is the patch (or subpatcher) name loaded into each voice.

        Example:
            >>> p.add_poly("mysynth", 8)   # -> "poly~ mysynth 8"
        """
        return self.add_textbox(f"poly~ {target} {voices}", **kwds)

    def add_coll(
        self,
        name: Optional[str] = None,
        dictionary: Optional[Dict[Any, Any]] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a coll object with option to pre-populate from a py dictionary."""
        extra = {"saved_object_attributes": {"embed": embed, "precision": 6}}
        if dictionary:
            extra["coll_data"] = {
                "count": len(dictionary.keys()),
                "data": [{"key": k, "value": v} for k, v in dictionary.items()],  # type: ignore
            }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id("coll"),
                text=text
                or (f"coll {name} @embed {embed}" if name else f"coll @embed {embed}"),
                maxclass="newobj",
                numinlets=1,
                numoutlets=4,
                outlettype=["", "", "", ""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_dict(
        self,
        name: Optional[str] = None,
        dictionary: Optional[Dict[Any, Any]] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a dict object with option to pre-populate from a py dictionary."""
        extra = {
            "saved_object_attributes": {
                "embed": embed,
                "parameter_enable": kwds.get("parameter_enable", 0),
                "parameter_mappable": kwds.get("parameter_mappable", 0),
            },
            "data": dictionary or {},
        }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id("dict"),
                text=text
                or (f"dict {name} @embed {embed}" if name else f"dict @embed {embed}"),
                maxclass="newobj",
                numinlets=2,
                numoutlets=4,
                outlettype=["dictionary", "", "", ""],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_table(
        self,
        name: Optional[str] = None,
        array: Optional[List[Union[int, float]]] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        tilde: bool = False,
        **kwds: Any,
    ) -> "Box":
        """Add a table object with option to pre-populate from a py list."""

        extra = {
            "embed": embed,
            "saved_object_attributes": {
                "name": name,
                "parameter_enable": kwds.get("parameter_enable", 0),
                "parameter_mappable": kwds.get("parameter_mappable", 0),
                "range": kwds.get("range", 128),
                "showeditor": 0,
                "size": len(array) if array else 128,
            },
            # "showeditor": 0,
            # 'size': kwds.get('size', 128),
            "table_data": array or [],
            "editor_rect": [100.0, 100.0, 300.0, 300.0],
        }
        kwds.update(extra)
        table_type = "table~" if tilde else "table"
        return self.add_box(
            Box(
                id=id or self.get_id(table_type),
                text=text
                or (
                    f"{table_type} {name} @embed {embed}"
                    if name
                    else f"{table_type} @embed {embed}"
                ),
                maxclass="newobj",
                numinlets=2,
                numoutlets=2,
                outlettype=["int", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_table_tilde(
        self,
        name: Optional[str] = None,
        array: Optional[List[Union[int, float]]] = None,
        embed: int = 1,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a table~ object with option to pre-populate from a py list."""

        return self.add_table(
            name,
            array,
            embed,
            patching_rect,
            text,
            id,
            comment,
            comment_pos,
            tilde=True,
            **kwds,
        )

    def add_itable(
        self,
        name: Optional[str] = None,
        array: Optional[List[Union[int, float]]] = None,
        patching_rect: Optional[Rect] = None,
        text: Optional[str] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a itable object with option to pre-populate from a py list."""

        extra = {
            "range": kwds.get("range", 128),
            "size": len(array) if array else 128,
            "table_data": array or [],
        }
        kwds.update(extra)
        return self.add_box(
            Box(
                id=id or self.get_id("itable"),
                text=text or f"itable {name}",
                maxclass="itable",
                numinlets=2,
                numoutlets=2,
                outlettype=["int", "bang"],
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_umenu(
        self,
        prefix: Optional[str] = None,
        autopopulate: int = 1,
        items: Optional[List[str]] = None,
        patching_rect: Optional[Rect] = None,
        depth: Optional[int] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a umenu object with option to pre-populate items from a py list."""

        # interleave commas in a list
        def _commas(xs: List[str]) -> List[str]:
            return [i for pair in zip(xs, [","] * len(xs)) for i in pair]

        return self.add_box(
            Box(
                id=id or self.get_id("umenu"),
                maxclass="umenu",
                numinlets=1,
                numoutlets=3,
                outlettype=["int", "", ""],
                autopopulate=autopopulate or 1,
                depth=depth or 1,
                items=_commas(cast(List[str], items)) or [],
                prefix=prefix or "",
                patching_rect=patching_rect or self.get_pos(),
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_bpatcher(
        self,
        name: str,
        numinlets: int = 1,
        numoutlets: int = 1,
        outlettype: Optional[List[str]] = None,
        bgmode: int = 0,
        border: int = 0,
        clickthrough: int = 0,
        enablehscroll: int = 0,
        enablevscroll: int = 0,
        lockeddragscroll: int = 0,
        offset: Optional[List[float]] = None,
        viewvisibility: int = 1,
        patching_rect: Optional[Rect] = None,
        id: Optional[str] = None,
        comment: Optional[str] = None,
        comment_pos: Optional[str] = None,
        **kwds: Any,
    ) -> "Box":
        """Add a bpatcher object -- name or patch of bpatcher .maxpat is required."""

        return self.add_box(
            Box(
                id=id or self.get_id("bpatcher"),
                name=name,
                maxclass="bpatcher",
                numinlets=numinlets,
                numoutlets=numoutlets,
                bgmode=bgmode,
                border=border,
                clickthrough=clickthrough,
                enablehscroll=enablehscroll,
                enablevscroll=enablevscroll,
                lockeddragscroll=lockeddragscroll,
                viewvisibility=viewvisibility,
                outlettype=outlettype or ["float", "", ""],
                patching_rect=patching_rect or self.get_pos(),
                offset=offset or [0.0, 0.0],
                **kwds,
            ),
            comment,
            comment_pos,
        )

    def add_beap(self, name: str, **kwds: Any) -> "Box":
        """Add a beap bpatcher object."""

        _varname = name if ".maxpat" not in name else name.removesuffix(".maxpat")
        return self.add_bpatcher(name=name, varname=_varname, extract=1, **kwds)
