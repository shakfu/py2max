"""Composable patcher transformers for py2max."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, NamedTuple, Optional, Sequence

from .core import Patcher
from .core.common import Rect

Transformer = Callable[[Patcher], Patcher]
TransformerFactory = Callable[[Optional[str]], Transformer]


class TransformerSpec(NamedTuple):
    factory: TransformerFactory
    description: str


def compose(transformers: Sequence[Transformer]) -> Transformer:
    """Compose multiple transformers into a single operation."""

    def _composed(patcher: Patcher) -> Patcher:
        current = patcher
        for transform in transformers:
            current = transform(current)
        return current

    return _composed


def run_pipeline(patcher: Patcher, transformers: Iterable[Transformer]) -> Patcher:
    """Apply each transformer in order to the patcher."""

    return compose(list(transformers))(patcher)


def optimize_layout(layout: str | None = None) -> Transformer:
    """Return a transformer that optimizes layout with an optional override."""

    def _transform(patcher: Patcher) -> Patcher:
        if layout:
            patcher._layout_mgr = patcher.set_layout_mgr(layout)
        patcher.optimize_layout()
        return patcher

    return _transform


def set_flow_direction(direction: str) -> Transformer:
    """Set the flow direction on the current layout manager."""

    def _transform(patcher: Patcher) -> Patcher:
        patcher._flow_direction = direction
        if hasattr(patcher._layout_mgr, "flow_direction"):
            patcher._layout_mgr.flow_direction = direction
        return patcher

    return _transform


def add_comment_transform(comment: str, pos: str = "above") -> Transformer:
    """Attach a comment near every object in the patcher."""

    def _transform(patcher: Patcher) -> Patcher:
        for box in list(patcher._boxes):
            if box.id:
                patcher.add_associated_comment(box, comment, comment_pos=pos)  # type: ignore[arg-type]
        patcher._process_pending_comments()
        return patcher

    return _transform


def set_font_size(size: float) -> Transformer:
    """Set default font size for the patcher and all boxes."""

    def _transform(patcher: Patcher) -> Patcher:
        patcher.default_fontsize = size
        for box in patcher._boxes:
            box._kwds["fontsize"] = size
        return patcher

    return _transform


def apply_theme_transform(theme: str) -> Transformer:
    """Return a transformer that applies a named color theme to the patcher."""

    def _transform(patcher: Patcher) -> Patcher:
        patcher.apply_theme(theme)
        return patcher

    return _transform


def scale_positions(factor: float) -> Transformer:
    """Return a transformer that scales every box's x/y position by ``factor``.

    Sizes are preserved -- only positions move -- so the patch spreads out
    (``factor`` > 1) or compacts (``factor`` < 1) without resizing objects.
    """

    def _transform(patcher: Patcher) -> Patcher:
        for box in patcher._boxes:
            rect = box.patching_rect
            box.patching_rect = Rect(
                rect[0] * factor, rect[1] * factor, rect[2], rect[3]
            )
        return patcher

    return _transform


def _set_font_size_factory(arg: Optional[str]) -> Transformer:
    value = float(arg) if arg is not None else 12.0
    return set_font_size(value)


_COMMENT_POSITIONS = ("above", "below", "left", "right")


def _add_comment_factory(arg: Optional[str]) -> Transformer:
    """Parse ``[pos:]text`` -- an optional position prefix, then the comment.

    e.g. ``below:my note`` places the comment below each box. A leading token
    that is not a known position is treated as part of the comment text, so
    ``"note: hi"`` is left intact and defaults to ``above``.
    """
    text = arg or "Auto"
    pos = "above"
    if ":" in text:
        head, rest = text.split(":", 1)
        if head.strip().lower() in _COMMENT_POSITIONS:
            pos, text = head.strip().lower(), rest
    return add_comment_transform(text, pos=pos)


def _optimize_layout_factory(arg: Optional[str]) -> Transformer:
    return optimize_layout(layout=arg)


def _set_flow_direction_factory(arg: Optional[str]) -> Transformer:
    direction = arg or "horizontal"
    return set_flow_direction(direction)


def _apply_theme_factory(arg: Optional[str]) -> Transformer:
    return apply_theme_transform(arg or "light")


def _scale_positions_factory(arg: Optional[str]) -> Transformer:
    factor = float(arg) if arg is not None else 1.5
    return scale_positions(factor)


_TRANSFORMERS: Dict[str, TransformerSpec] = {
    "set-font-size": TransformerSpec(
        _set_font_size_factory, "Set default font size (points). Default 12.0"
    ),
    "add-comment": TransformerSpec(
        _add_comment_factory,
        "Attach a comment near each box; optional position prefix "
        "'above|below|left|right:text' (default above)",
    ),
    "apply-theme": TransformerSpec(
        _apply_theme_factory,
        "Apply a named color theme to all boxes (light/dark/blue/high-contrast)",
    ),
    "scale-positions": TransformerSpec(
        _scale_positions_factory,
        "Scale every object's x/y position by a factor (default 1.5); sizes unchanged",
    ),
    "optimize-layout": TransformerSpec(
        _optimize_layout_factory,
        "Run layout optimisation (optionally specify layout name)",
    ),
    "set-flow-direction": TransformerSpec(
        _set_flow_direction_factory,
        "Adjust flow direction for the active layout manager (horizontal/vertical/column)",
    ),
}


def available_transformers() -> Dict[str, str]:
    """Return available transformer names mapped to short descriptions."""

    return {name: spec.description for name, spec in _TRANSFORMERS.items()}


def create_transformer(name: str, argument: Optional[str] = None) -> Transformer:
    """Instantiate a transformer by name.

    Args:
        name: Registered transformer name.
        argument: Optional string argument passed to the transformer factory.

    Raises:
        KeyError: If the transformer name is unknown.
        ValueError: If the argument cannot be parsed.
    """

    try:
        spec = _TRANSFORMERS[name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(f"Unknown transformer '{name}'") from exc

    try:
        return spec.factory(argument)
    except ValueError as exc:  # pragma: no cover - argument parsing failure
        raise ValueError(
            f"Invalid argument for transformer '{name}': {argument}"
        ) from exc


__all__ = [
    "Transformer",
    "TransformerFactory",
    "TransformerSpec",
    "compose",
    "run_pipeline",
    "optimize_layout",
    "set_flow_direction",
    "add_comment_transform",
    "set_font_size",
    "apply_theme_transform",
    "scale_positions",
    "available_transformers",
    "create_transformer",
]
