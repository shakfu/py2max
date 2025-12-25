"""Backward compatibility shim for py2max.repl_inline module.

This module re-exports from py2max.server.inline for backward compatibility.
New code should import directly from py2max.server.
"""

from .server.inline import (
    BackgroundServerREPL,
    restore_console_logging,
    setup_file_logging,
    start_background_server_repl,
    start_inline_repl,
)

__all__ = [
    "BackgroundServerREPL",
    "start_inline_repl",
    "start_background_server_repl",
    "setup_file_logging",
    "restore_console_logging",
]
