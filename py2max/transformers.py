"""Composable patcher transformers for py2max."""

from __future__ import annotations

from typing import Callable, Iterable, Sequence

from .core import Patcher

Transformer = Callable[[Patcher], Patcher]


def compose(transformers: Sequence[Transformer]) -> Transformer:
    """Compose multiple transformers into a single operation."""

    def _composed(patcher: Patcher) -> Patcher:
        current = patcher
        for transform in transformers:
            current = transform(current)
        return current

    return _composed


def run_pipeline(patcher: Patcher, transformers: Iterable[Transformer]) -> Patcher:
    current = patcher
    for transform in transformers:
        current = transform(current)
    return current


def optimize_layout(layout: str | None = None, flow_direction: str | None = None) -> Transformer:
    """Return a transformer that optimizes layout with optional overrides."""

    def _transform(patcher: Patcher) -> Patcher:
        if layout:
            patcher._layout_mgr = patcher.set_layout_mgr(layout)
        if flow_direction:
            patcher._flow_direction = flow_direction
            if hasattr(patcher._layout_mgr, "flow_direction"):
                patcher._layout_mgr.flow_direction = flow_direction
        patcher.optimize_layout()
        return patcher

    return _transform


def add_comment_transform(comment: str, pos: str = "above") -> Transformer:
    """Add a comment next to every box."""

    def _transform(patcher: Patcher) -> Patcher:
        for box in list(patcher._boxes):
            if box.id:
                patcher.add_associated_comment(box, comment, comment_pos=pos)
        patcher._process_pending_comments()
        return patcher

    return _transform


def set_font_size(size: float) -> Transformer:
    """Set default font size for patcher and existing boxes."""

    def _transform(patcher: Patcher) -> Patcher:
        patcher.default_fontsize = size
        for box in patcher._boxes:
            box._kwds["fontsize"] = size
        return patcher

    return _transform

