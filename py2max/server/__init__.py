"""Interactive server and REPL for py2max.

This subpackage provides WebSocket-based server and REPL functionality
for real-time interactive editing of Max patches.

Modules:
- websocket: WebSocket server for bidirectional communication
- repl: Interactive REPL using ptpython
- client: Remote REPL client
- inline: Inline REPL with background server
- rpc: Remote procedure call server for REPL
"""

from .websocket import (
    InteractivePatcherServer,
    InteractiveWebSocketHandler,
    get_patcher_state_json,
    serve_interactive,
)
from .repl import AutoSyncWrapper, ReplCommands, start_repl, start_repl_with_refresh
from .client import ReplClient, start_repl_client
from .inline import (
    BackgroundServerREPL,
    restore_console_logging,
    setup_file_logging,
    start_background_server_repl,
    start_inline_repl,
)
from .rpc import ReplServer, start_repl_server

__all__ = [
    # WebSocket server
    "InteractivePatcherServer",
    "InteractiveWebSocketHandler",
    "get_patcher_state_json",
    "serve_interactive",
    # REPL
    "AutoSyncWrapper",
    "ReplCommands",
    "start_repl",
    "start_repl_with_refresh",
    # Client
    "ReplClient",
    "start_repl_client",
    # Inline
    "BackgroundServerREPL",
    "start_inline_repl",
    "start_background_server_repl",
    "setup_file_logging",
    "restore_console_logging",
    # RPC
    "ReplServer",
    "start_repl_server",
]
