"""Interactive WebSocket server for py2max with bidirectional communication.

This module provides a WebSocket-based server for real-time interactive
editing of Max patches in the browser.

Features:
    - Bidirectional WebSocket communication
    - Real-time updates (Python → Browser)
    - Interactive editing (Browser → Python)
    - Drag-and-drop object repositioning
    - Connection drawing
    - Object creation from browser

Example:
    >>> from py2max import Patcher
    >>> p = Patcher('demo.maxpat')
    >>> await p.serve_interactive()  # Opens browser with interactive editor
    >>> # Edit in browser - changes sync back to Python!
"""

from __future__ import annotations

import asyncio
import json
import webbrowser
import http.server
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Set

try:
    import websockets
    from websockets.asyncio.server import ServerConnection, serve
except ImportError:
    raise ImportError(
        "websockets package required for interactive server. "
        "Install with: pip install websockets"
    )

if TYPE_CHECKING:
    from .core import Patcher


def get_patcher_state_json(patcher: Optional['Patcher']) -> dict:
    """Convert patcher to JSON state for browser.

    Args:
        patcher: The patcher to convert

    Returns:
        Dictionary with boxes and lines data
    """
    if not patcher:
        return {'type': 'update', 'boxes': [], 'lines': []}

    boxes = []
    for box in patcher._boxes:
        box_data = {
            'id': getattr(box, 'id', ''),
            'text': getattr(box, 'text', ''),
            'maxclass': getattr(box, 'maxclass', 'newobj'),
            'patching_rect': {
                'x': 0, 'y': 0, 'w': 100, 'h': 22
            }
        }

        # Get patching_rect
        rect = getattr(box, 'patching_rect', None)
        if rect:
            if hasattr(rect, 'x'):
                box_data['patching_rect'] = {
                    'x': rect.x, 'y': rect.y, 'w': rect.w, 'h': rect.h
                }
            elif isinstance(rect, (list, tuple)) and len(rect) >= 4:
                box_data['patching_rect'] = {
                    'x': rect[0], 'y': rect[1], 'w': rect[2], 'h': rect[3]
                }

        # Get inlet/outlet counts
        if hasattr(box, 'get_inlet_count'):
            try:
                box_data['inlet_count'] = box.get_inlet_count() or 0
            except Exception:
                box_data['inlet_count'] = 0
        else:
            box_data['inlet_count'] = 0

        if hasattr(box, 'get_outlet_count'):
            try:
                box_data['outlet_count'] = box.get_outlet_count() or 0
            except Exception:
                box_data['outlet_count'] = 0
        else:
            box_data['outlet_count'] = 0

        boxes.append(box_data)

    lines = []
    for line in patcher._lines:
        line_data = {
            'src': getattr(line, 'src', ''),
            'dst': getattr(line, 'dst', ''),
            'src_outlet': 0,
            'dst_inlet': 0
        }

        source = getattr(line, 'source', None)
        if source and len(source) > 1:
            line_data['src_outlet'] = source[1]

        destination = getattr(line, 'destination', None)
        if destination and len(destination) > 1:
            line_data['dst_inlet'] = destination[1]

        lines.append(line_data)

    return {
        'type': 'update',
        'boxes': boxes,
        'lines': lines
    }


class InteractiveHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for serving static files."""

    def __init__(self, *args, **kwargs):
        static_dir = Path(__file__).parent / 'static'
        super().__init__(*args, directory=str(static_dir), **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/' or self.path == '/index.html':
            self.serve_interactive_html()
        else:
            super().do_GET()

    def serve_interactive_html(self):
        """Serve the interactive editor HTML."""
        html_file = Path(__file__).parent / 'static' / 'interactive.html'
        if html_file.exists():
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(html_file.read_bytes())
        else:
            self.send_error(404, "interactive.html not found")

    def log_message(self, format, *args):
        """Suppress logging."""
        pass


class InteractiveWebSocketHandler:
    """WebSocket handler for interactive patcher editing."""

    def __init__(self, patcher: Optional['Patcher'], auto_save: bool = False):
        self.patcher = patcher
        self.clients: Set[ServerConnection] = set()
        self._lock = asyncio.Lock()
        self._save_task = None  # Track pending save task for debouncing
        self.auto_save = auto_save  # Auto-save configuration

    async def register(self, websocket: ServerConnection):
        """Register a new client connection."""
        async with self._lock:
            self.clients.add(websocket)
            print(f"Client connected. Total clients: {len(self.clients)}")

    async def unregister(self, websocket: ServerConnection):
        """Unregister a client connection."""
        async with self._lock:
            self.clients.discard(websocket)
            print(f"Client disconnected. Total clients: {len(self.clients)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        if not self.clients:
            return

        message_str = json.dumps(message)
        async with self._lock:
            # Send to all clients concurrently
            await asyncio.gather(
                *[client.send(message_str) for client in self.clients],
                return_exceptions=True
            )

    async def handle_client(self, websocket: ServerConnection):
        """Handle a client WebSocket connection."""
        await self.register(websocket)

        try:
            # Send initial state
            if self.patcher:
                state = get_patcher_state_json(self.patcher)
                await websocket.send(json.dumps(state))

            # Listen for messages from client
            async for message in websocket:
                msg_str = message.decode('utf-8') if isinstance(message, bytes) else message
                await self.handle_message(websocket, msg_str)

        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)

    async def handle_message(self, websocket: ServerConnection, message: str):
        """Handle incoming message from client."""
        try:
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'update_position':
                await self.handle_update_position(data)
            elif message_type == 'create_object':
                await self.handle_create_object(data)
            elif message_type == 'create_connection':
                await self.handle_create_connection(data)
            elif message_type == 'delete_object':
                await self.handle_delete_object(data)
            elif message_type == 'delete_connection':
                await self.handle_delete_connection(data)
            elif message_type == 'save':
                await self.handle_save()
            else:
                print(f"Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
        except Exception as e:
            print(f"Error handling message: {e}")

    async def handle_update_position(self, data: dict):
        """Handle object position update from browser."""
        if not self.patcher:
            return

        box_id = data.get('box_id')
        x = data.get('x')
        y = data.get('y')

        # Find box and update position
        for box in self.patcher._boxes:
            if box.id == box_id:
                # Update position
                if hasattr(box, 'patching_rect'):
                    rect = box.patching_rect
                    if hasattr(rect, 'x'):
                        # Rect is a NamedTuple (immutable), create new one
                        from .common import Rect
                        box.patching_rect = Rect(float(x) if x is not None else 0.0,
                                                  float(y) if y is not None else 0.0,
                                                  rect.w, rect.h)
                    elif isinstance(rect, list):
                        rect[0] = x
                        rect[1] = y

                # Broadcast update to all clients
                state = get_patcher_state_json(self.patcher)
                await self.broadcast(state)

                # Schedule debounced save
                await self.schedule_save()
                break

    async def schedule_save(self):
        """Schedule a debounced save after 2 seconds of no updates (if auto-save enabled)."""
        if not self.auto_save:
            return  # Auto-save disabled

        # Cancel previous save task if exists
        if self._save_task and not self._save_task.done():
            self._save_task.cancel()

        # Schedule new save task
        self._save_task = asyncio.create_task(self._debounced_save())

    async def _debounced_save(self):
        """Save patch after delay (debounced)."""
        try:
            await asyncio.sleep(2.0)  # Wait 2 seconds
            if self.patcher and hasattr(self.patcher, 'filepath') and self.patcher.filepath:
                self.patcher.save()
                print(f"Auto-saved: {self.patcher.filepath}")
        except asyncio.CancelledError:
            # Task was cancelled (new position update came in)
            pass
        except Exception as e:
            print(f"Error during auto-save: {e}")

    async def handle_create_object(self, data: dict):
        """Handle object creation from browser."""
        if not self.patcher:
            return

        text = data.get('text', 'newobj')
        x = data.get('x', 100)
        y = data.get('y', 100)

        # Create new object
        box = self.patcher.add_textbox(text)

        # Set position
        if hasattr(box, 'patching_rect'):
            rect = box.patching_rect
            if hasattr(rect, 'x'):
                # Rect is a NamedTuple (immutable), create new one
                from .common import Rect
                box.patching_rect = Rect(x, y, rect.w, rect.h)
            elif isinstance(rect, list):
                rect[0] = x
                rect[1] = y

        # Broadcast update to all clients
        state = get_patcher_state_json(self.patcher)
        await self.broadcast(state)

        # Schedule auto-save
        await self.schedule_save()

    async def handle_create_connection(self, data: dict):
        """Handle connection creation from browser."""
        if not self.patcher:
            return

        src_id = data.get('src_id')
        dst_id = data.get('dst_id')
        src_outlet = data.get('src_outlet', 0)
        dst_inlet = data.get('dst_inlet', 0)

        # Find source and destination boxes
        src_box = None
        dst_box = None

        for box in self.patcher._boxes:
            if box.id == src_id:
                src_box = box
            if box.id == dst_id:
                dst_box = box

        if src_box and dst_box:
            # Create connection
            self.patcher.add_line(src_box, dst_box, outlet=src_outlet, inlet=dst_inlet)  # type: ignore[arg-type]

            # Broadcast update to all clients
            state = get_patcher_state_json(self.patcher)
            await self.broadcast(state)

            # Schedule auto-save
            await self.schedule_save()

    async def handle_delete_object(self, data: dict):
        """Handle object deletion from browser."""
        if not self.patcher:
            return

        box_id = data.get('box_id')

        # Find and remove box
        for i, box in enumerate(self.patcher._boxes):
            if box.id == box_id:
                self.patcher._boxes.pop(i)

                # Also remove any connected lines
                self.patcher._lines = [
                    line for line in self.patcher._lines
                    if line.src != box_id and line.dst != box_id
                ]

                # Broadcast update to all clients
                state = get_patcher_state_json(self.patcher)
                await self.broadcast(state)

                # Schedule auto-save
                await self.schedule_save()
                break

    async def handle_delete_connection(self, data: dict):
        """Handle connection deletion from browser."""
        if not self.patcher:
            return

        src_id = data.get('src_id')
        dst_id = data.get('dst_id')
        src_outlet = data.get('src_outlet', 0)
        dst_inlet = data.get('dst_inlet', 0)

        # Find and remove matching line
        for i, line in enumerate(self.patcher._lines):
            if (line.src == src_id and line.dst == dst_id and
                line.source[1] == src_outlet and line.destination[1] == dst_inlet):  # type: ignore[attr-defined]
                self.patcher._lines.pop(i)

                # Broadcast update to all clients
                state = get_patcher_state_json(self.patcher)
                await self.broadcast(state)

                # Schedule auto-save
                await self.schedule_save()
                break

    async def handle_save(self):
        """Handle manual save request from browser."""
        if not self.patcher:
            return

        try:
            if hasattr(self.patcher, 'filepath') and self.patcher.filepath:
                self.patcher.save()
                print(f"Saved: {self.patcher.filepath}")

                # Notify clients that save completed
                await self.broadcast({
                    'type': 'save_complete',
                    'filepath': str(self.patcher.filepath)
                })
            else:
                print("Warning: No filepath set, cannot save")
                await self.broadcast({
                    'type': 'save_error',
                    'message': 'No filepath set'
                })
        except Exception as e:
            print(f"Error saving: {e}")
            await self.broadcast({
                'type': 'save_error',
                'message': str(e)
            })

    async def notify_update(self):
        """Notify all clients of a patcher update."""
        if self.patcher:
            state = get_patcher_state_json(self.patcher)
            await self.broadcast(state)


class InteractivePatcherServer:
    """WebSocket server for interactive patcher editing.

    Can be used as a context manager for automatic cleanup:

        >>> async with p.serve_interactive() as server:
        ...     await asyncio.sleep(10)  # Server runs
        # Server automatically stopped
    """

    def __init__(self, patcher: 'Patcher', port: int = 8000, auto_open: bool = True, auto_save: bool = False):
        """Initialize the interactive server.

        Args:
            patcher: Patcher instance to serve
            port: HTTP/WebSocket server port (default: 8000)
            auto_open: Automatically open browser (default: True)
            auto_save: Automatically save changes after 2 seconds (default: False)
        """
        self.patcher = patcher
        self.port = port
        self.ws_port = port + 1  # WebSocket on different port
        self.auto_open = auto_open
        self.handler = InteractiveWebSocketHandler(patcher, auto_save=auto_save)
        self.ws_server = None
        self.http_server = None
        self.http_thread = None
        self._running = False

    async def start(self):
        """Start the HTTP and WebSocket servers.

        Returns:
            self: For method chaining
        """
        if self._running:
            print("Server already running")
            return self

        # Start HTTP server in background thread
        self.http_server = http.server.HTTPServer(
            ('localhost', self.port),
            InteractiveHTTPHandler
        )
        self.http_thread = threading.Thread(
            target=self.http_server.serve_forever,
            daemon=True
        )
        self.http_thread.start()

        # Start WebSocket server
        self.ws_server = await serve(
            self.handler.handle_client,
            'localhost',
            self.ws_port
        )
        self._running = True

        url = f"http://localhost:{self.port}"
        print(f"Interactive server started: {url}")
        print(f"WebSocket endpoint: ws://localhost:{self.ws_port}/ws")

        # Open browser
        if self.auto_open:
            await asyncio.sleep(0.5)  # Give server time to start
            webbrowser.open(url)

        return self

    async def stop(self):
        """Stop the servers."""
        await self.shutdown()

    async def shutdown(self):
        """Shutdown the servers gracefully."""
        if not self._running:
            return

        # Stop WebSocket server
        if self.ws_server:
            self.ws_server.close()
            await self.ws_server.wait_closed()

        # Stop HTTP server
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()

        self._running = False
        print("Interactive server stopped")

        # Clear clients
        self.handler.clients.clear()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()
        return False

    async def notify_update(self):
        """Notify all connected clients of an update."""
        await self.handler.notify_update()


async def serve_interactive(
    patcher: 'Patcher',
    port: int = 8000,
    auto_open: bool = True,
    auto_save: bool = False
) -> InteractivePatcherServer:
    """Start an interactive WebSocket server for a patcher.

    The server can be used as an async context manager:

        >>> async with serve_interactive(p) as server:
        ...     await asyncio.sleep(10)
        # Server automatically stopped

    Or managed manually:

        >>> server = await serve_interactive(p)
        >>> # ... interact ...
        >>> await server.shutdown()

    Args:
        patcher: Patcher instance to serve
        port: WebSocket server port (default: 8000)
        auto_open: Automatically open browser (default: True)
        auto_save: Automatically save changes after 2 seconds (default: False)

    Returns:
        InteractivePatcherServer instance
    """
    server = InteractivePatcherServer(patcher, port, auto_open, auto_save)
    await server.start()
    return server


__all__ = [
    'InteractiveWebSocketHandler',
    'InteractivePatcherServer',
    'serve_interactive',
]
