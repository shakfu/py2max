"""Layout management for py2max patches.

This subpackage provides various layout managers for automatic positioning of
Max objects in patches:

- LayoutManager: Basic horizontal layout (deprecated)
- GridLayoutManager: Grid-based layout with clustering
- FlowLayoutManager: Signal flow-based hierarchical layout
- MatrixLayoutManager: Matrix/columnar layout for signal chains
- HorizontalLayoutManager: Legacy alias for GridLayoutManager (horizontal)
- VerticalLayoutManager: Legacy alias for GridLayoutManager (vertical)
"""

from .base import LayoutManager
from .flow import FlowLayoutManager
from .grid import GridLayoutManager, HorizontalLayoutManager, VerticalLayoutManager
from .matrix import MatrixLayoutManager

__all__ = [
    "LayoutManager",
    "GridLayoutManager",
    "HorizontalLayoutManager",
    "VerticalLayoutManager",
    "FlowLayoutManager",
    "MatrixLayoutManager",
]
