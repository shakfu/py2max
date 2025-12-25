"""Backward compatibility shim for py2max.svg module.

This module re-exports from py2max.export.svg for backward compatibility.
New code should import directly from py2max.export.
"""

from .export.svg import export_svg, export_svg_string

__all__ = ["export_svg", "export_svg_string"]
