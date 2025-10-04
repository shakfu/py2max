"""Composable patcher transformers for py2max."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, NamedTuple, Optional, Sequence

from .core import Patcher

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

    current = patcher
    for transform in transformers:
        current = transform(current)
    return current


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
                patcher.add_associated_comment(box, comment, comment_pos=pos)
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


def _set_font_size_factory(arg: Optional[str]) -> Transformer:
    value = float(arg) if arg is not None else 12.0
    return set_font_size(value)


def _add_comment_factory(arg: Optional[str]) -> Transformer:
    text = arg or "Auto"
    return add_comment_transform(text)


def _optimize_layout_factory(arg: Optional[str]) -> Transformer:
    return optimize_layout(layout=arg)


def _set_flow_direction_factory(arg: Optional[str]) -> Transformer:
    direction = arg or "horizontal"
    return set_flow_direction(direction)


_TRANSFORMERS: Dict[str, TransformerSpec] = {
    "set-font-size": TransformerSpec(
        _set_font_size_factory, "Set default font size (points). Default 12.0"
    ),
    "add-comment": TransformerSpec(
        _add_comment_factory, "Attach the supplied comment text above each box"
    ),
    "optimize-layout": TransformerSpec(
        _optimize_layout_factory, "Run layout optimisation (optionally specify layout name)"
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
        raise ValueError(f"Invalid argument for transformer '{name}': {argument}") from exc


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
    "available_transformers",
    "create_transformer",
]
