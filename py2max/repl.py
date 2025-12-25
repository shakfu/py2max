"""Backward compatibility shim for py2max.repl module.

This module re-exports from py2max.server.repl for backward compatibility.
New code should import directly from py2max.server.
"""

from .server.repl import (
    AutoSyncWrapper,
    ReplCommands,
    start_repl,
    start_repl_with_refresh,
)

# Re-export embed for tests that patch it
try:
    from ptpython.repl import embed
except ImportError:
    embed = None  # type: ignore

__all__ = [
    "AutoSyncWrapper",
    "ReplCommands",
    "embed",
    "start_repl",
    "start_repl_with_refresh",
]
