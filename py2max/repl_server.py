"""Backward compatibility shim for py2max.repl_server module.

This module re-exports from py2max.server.rpc for backward compatibility.
New code should import directly from py2max.server.
"""

from .server.rpc import ReplServer, start_repl_server

__all__ = ["ReplServer", "start_repl_server"]
