"""Backward compatibility shim for py2max.repl_client module.

This module re-exports from py2max.server.client for backward compatibility.
New code should import directly from py2max.server.
"""

from .server.client import ReplClient, start_repl_client

# Re-export connect for tests that patch it
try:
    from websockets.asyncio.client import connect
except ImportError:
    connect = None  # type: ignore

__all__ = ["ReplClient", "start_repl_client", "connect"]
