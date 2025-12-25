"""Remote REPL server for py2max.

This module provides a WebSocket-based RPC server that allows remote
REPL clients to execute code against a running patcher instance.

The server listens on a separate port (default: 9000) and executes
code sent by REPL clients, returning results.
"""

from __future__ import annotations

import asyncio
import json
import sys
import traceback as tb
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from ..core import Patcher
    from .websocket import InteractivePatcherServer

try:
    import websockets
    from websockets.asyncio.server import ServerConnection, serve
except ImportError:
    raise ImportError(
        "websockets package required for REPL server. "
        "Install with: pip install websockets"
    )


class ReplServer:
    """WebSocket-based REPL server for remote code execution."""

    def __init__(self, patcher: "Patcher", server: "InteractivePatcherServer"):
        self.patcher = patcher
        self.server = server
        self.clients: set[ServerConnection] = set()
        self._lock = asyncio.Lock()

        # Build execution namespace with patcher and commands
        from .repl import ReplCommands

        self.commands = ReplCommands(patcher, server)
        self.namespace: Dict[str, Any] = {
            "p": patcher,
            "patcher": patcher,
            "server": server,
            "asyncio": asyncio,
            # Command functions
            "save": self.commands.save,
            "info": self.commands.info,
            "layout": self.commands.layout,
            "optimize": self.commands.optimize,
            "clear": self.commands.clear,
            "clients": self.commands.clients,
            "help_obj": self.commands.help_obj,
            "commands": self.commands.commands,
        }

    async def handle_client(self, websocket: ServerConnection):
        """Handle REPL client connection."""
        async with self._lock:
            self.clients.add(websocket)
            print(f"REPL client connected (total: {len(self.clients)})")

        try:
            async for message in websocket:
                msg_str = (
                    message.decode("utf-8") if isinstance(message, bytes) else message
                )
                await self.handle_message(websocket, msg_str)

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            async with self._lock:
                self.clients.discard(websocket)
                print(f"REPL client disconnected (total: {len(self.clients)})")

    async def handle_message(self, websocket: ServerConnection, message: str):
        """Handle message from REPL client."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "init":
                await self.handle_init(websocket)
            elif msg_type == "eval":
                await self.handle_eval(websocket, data)
            else:
                await websocket.send(
                    json.dumps(
                        {"type": "error", "error": f"Unknown message type: {msg_type}"}
                    )
                )

        except json.JSONDecodeError as e:
            await websocket.send(
                json.dumps({"type": "error", "error": f"Invalid JSON: {e}"})
            )
        except Exception as e:
            await websocket.send(
                json.dumps({"type": "error", "error": f"Error handling message: {e}"})
            )

    async def handle_init(self, websocket: ServerConnection):
        """Handle initialization request from client."""
        # Send patcher info
        info = {
            "patcher_path": str(self.patcher.filepath)
            if self.patcher.filepath
            else "Untitled",
            "num_objects": len(self.patcher._boxes),
            "num_connections": len(self.patcher._lines),
        }

        await websocket.send(json.dumps({"type": "init_response", "info": info}))

    async def handle_eval(self, websocket: ServerConnection, data: dict):
        """Handle code evaluation request."""
        code = data.get("code", "")
        # mode = data.get("mode", "exec")  # Reserved for future "exec" or "eval" mode

        if not code.strip():
            await websocket.send(
                json.dumps({"type": "result", "result": None, "display": None})
            )
            return

        # Capture output
        output_lines = []

        class OutputCapture:
            def write(self, text):
                output_lines.append(text)

            def flush(self):
                pass

        # Redirect stdout temporarily
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = OutputCapture()
        sys.stderr = OutputCapture()

        try:
            # Try eval first (for expressions)
            try:
                result = eval(code, self.namespace)

                # Handle async results
                if asyncio.iscoroutine(result):
                    result = await result

                # Get string representation
                result_str = repr(result) if result is not None else None

                # Get captured output
                display = "".join(output_lines) if output_lines else None

                await websocket.send(
                    json.dumps(
                        {
                            "type": "result",
                            "result": result_str,
                            "display": display,
                        }
                    )
                )

            except SyntaxError:
                # Fall back to exec (for statements)
                exec(code, self.namespace)

                # Get captured output
                display = "".join(output_lines) if output_lines else None

                await websocket.send(
                    json.dumps(
                        {
                            "type": "result",
                            "result": None,
                            "display": display,
                        }
                    )
                )

        except Exception as e:
            # Get traceback
            traceback_str = tb.format_exc()

            await websocket.send(
                json.dumps(
                    {
                        "type": "error",
                        "error": str(e),
                        "traceback": traceback_str,
                    }
                )
            )

        finally:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr


async def start_repl_server(
    patcher: "Patcher",
    server: "InteractivePatcherServer",
    port: int = 9000,
) -> Any:
    """Start REPL server.

    Args:
        patcher: Patcher instance
        server: WebSocket server instance
        port: REPL server port (default: 9000)

    Returns:
        Server instance
    """
    repl_server = ReplServer(patcher, server)

    # Start WebSocket server
    ws_server = await serve(
        repl_server.handle_client,
        "localhost",
        port,
    )

    print(f"REPL server started on port {port}")
    print(f"Connect with: py2max repl localhost:{port}")
    print()

    return ws_server


__all__ = ["ReplServer", "start_repl_server"]
