"""Live preview server for py2max using Server-Sent Events (SSE).

This module provides a pure Python stdlib-based server for real-time
visualization of Max patches as they're created in the REPL.

Features:
    - Real-time updates via Server-Sent Events (SSE)
    - Pure Python stdlib (no dependencies)
    - Automatic browser opening
    - Live SVG rendering

Example:
    >>> from py2max import Patcher
    >>> p = Patcher('demo.maxpat')
    >>> p.serve()  # Opens browser with live preview
    >>> osc = p.add_textbox('cycle~ 440')  # Updates browser
    >>> gain = p.add_textbox('gain~')      # Updates browser
    >>> p.add_line(osc, gain)              # Updates browser
"""

from __future__ import annotations

import http.server
import json
import threading
import time
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Optional, List, Set
from queue import Queue, Empty

if TYPE_CHECKING:
    from .core import Patcher


def get_patcher_state_json(patcher: Optional['Patcher']) -> dict:
    """Convert patcher to JSON state for browser.

    This is a standalone function so it can be called without creating
    a handler instance.
    """
    if not patcher:
        return {'type': 'update', 'boxes': [], 'lines': []}

    boxes = []
    for box in patcher._boxes:
        box_data = {
            'id': getattr(box, 'id', ''),
            'text': getattr(box, 'text', ''),
            'maxclass': getattr(box, 'maxclass', 'newobj'),
        }

        # Get position
        rect = getattr(box, 'patching_rect', None)
        if rect:
            if hasattr(rect, 'x'):
                box_data.update({
                    'x': rect.x,
                    'y': rect.y,
                    'width': rect.w,
                    'height': rect.h,
                })
            elif isinstance(rect, (list, tuple)) and len(rect) >= 4:
                box_data.update({
                    'x': rect[0],
                    'y': rect[1],
                    'width': rect[2],
                    'height': rect[3],
                })

        # Get inlet/outlet counts
        if hasattr(box, 'get_inlet_count'):
            try:
                box_data['inlet_count'] = box.get_inlet_count() or 0
            except:
                box_data['inlet_count'] = 0
        else:
            box_data['inlet_count'] = 0

        if hasattr(box, 'get_outlet_count'):
            try:
                box_data['outlet_count'] = box.get_outlet_count() or 0
            except:
                box_data['outlet_count'] = 0
        else:
            box_data['outlet_count'] = 0

        boxes.append(box_data)

    lines = []
    for line in patcher._lines:
        line_data = {
            'src': getattr(line, 'src', ''),
            'dst': getattr(line, 'dst', ''),
        }

        source = getattr(line, 'source', [])
        destination = getattr(line, 'destination', [])

        if len(source) > 1:
            line_data['src_outlet'] = int(source[1])
        else:
            line_data['src_outlet'] = 0

        if len(destination) > 1:
            line_data['dst_inlet'] = int(destination[1])
        else:
            line_data['dst_inlet'] = 0

        lines.append(line_data)

    return {
        'type': 'update',
        'boxes': boxes,
        'lines': lines,
        'title': getattr(patcher, 'title', 'Untitled Patch'),
    }


class SSEHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with Server-Sent Events support."""

    # Class-level shared state
    patcher: Optional['Patcher'] = None
    event_queues: Set[Queue] = set()
    _lock = threading.Lock()

    def __init__(self, *args, **kwargs):
        # Serve static files from the server's static directory
        self.static_dir = Path(__file__).parent / 'static'
        super().__init__(*args, directory=str(self.static_dir), **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/events':
            self.handle_sse()
        elif self.path == '/state':
            self.handle_state()
        elif self.path == '/' or self.path == '/index.html':
            self.serve_index()
        else:
            super().do_GET()

    def handle_sse(self):
        """Handle Server-Sent Events connection."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Create a queue for this client
        client_queue: Queue = Queue()

        with self._lock:
            self.event_queues.add(client_queue)

        try:
            # Send initial state
            if self.patcher:
                initial_state = self.get_patcher_state()
                self.send_event(initial_state)

            # Keep connection alive and send updates
            while True:
                try:
                    # Wait for updates (with timeout to detect client disconnect)
                    event_data = client_queue.get(timeout=30)
                    self.send_event(event_data)
                except Empty:
                    # Send keepalive comment
                    self.wfile.write(b': keepalive\n\n')
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    break

        finally:
            with self._lock:
                self.event_queues.discard(client_queue)

    def send_event(self, data: dict):
        """Send an SSE event to the client."""
        event_text = f"data: {json.dumps(data)}\n\n"
        self.wfile.write(event_text.encode('utf-8'))
        self.wfile.flush()

    def handle_state(self):
        """Handle request for current patcher state."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        state = self.get_patcher_state()
        self.wfile.write(json.dumps(state).encode('utf-8'))

    def get_patcher_state(self) -> dict:
        """Convert patcher to JSON state for browser."""
        return get_patcher_state_json(self.patcher)

    def serve_index(self):
        """Serve the main HTML page."""
        html_content = self.get_index_html()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def get_index_html(self) -> str:
        """Get the HTML content for the live preview page."""
        # Check if static file exists
        static_file = Path(__file__).parent / 'static' / 'index.html'
        if static_file.exists():
            return static_file.read_text()

        # Otherwise return embedded HTML
        return '''<!DOCTYPE html>
<html>
<head>
    <title>py2max Live Preview</title>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: Monaco, Courier, monospace;
            background: #1e1e1e;
            color: #d4d4d4;
        }
        #header {
            background: #2d2d2d;
            padding: 15px;
            border-bottom: 2px solid #4080ff;
        }
        h1 {
            margin: 0;
            font-size: 18px;
            color: #4080ff;
        }
        #status {
            position: fixed;
            top: 15px;
            right: 15px;
            padding: 8px 16px;
            background: #2d2d2d;
            border-radius: 4px;
            font-size: 12px;
        }
        .connected { color: #0f0; }
        .disconnected { color: #f00; }
        #canvas {
            padding: 20px;
            overflow: auto;
            height: calc(100vh - 80px);
        }
        svg {
            background: white;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .box rect {
            cursor: pointer;
        }
        .box:hover rect {
            stroke: #4080ff;
            stroke-width: 2;
        }
        #info {
            position: fixed;
            bottom: 15px;
            right: 15px;
            padding: 8px 16px;
            background: #2d2d2d;
            border-radius: 4px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div id="header">
        <h1 id="title">py2max Live Preview</h1>
    </div>
    <div id="status" class="disconnected">Connecting...</div>
    <div id="canvas"></div>
    <div id="info"></div>
    <script src="live-preview.js"></script>
</body>
</html>'''

    def log_message(self, format, *args):
        """Suppress logging unless verbose mode."""
        pass  # Suppress standard logging


class PatcherServer:
    """Server for live patcher preview using SSE.

    Can be used as a context manager for automatic cleanup:

        >>> with p.serve() as server:
        ...     # Server runs in background
        ...     p.add_textbox('cycle~ 440')
        ...     p.save()
        # Server automatically stopped
    """

    def __init__(self, patcher: 'Patcher', port: int = 8000, auto_open: bool = True):
        """Initialize the server.

        Args:
            patcher: Patcher instance to serve
            port: HTTP server port (default: 8000)
            auto_open: Automatically open browser (default: True)
        """
        self.patcher = patcher
        self.port = port
        self.auto_open = auto_open
        self.server: Optional[http.server.HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        """Start the server in a background thread.

        Returns:
            self: For method chaining
        """
        if self._running:
            print("Server already running")
            return self

        # Set class-level patcher reference
        SSEHandler.patcher = self.patcher

        # Create server
        self.server = http.server.HTTPServer(('localhost', self.port), SSEHandler)

        # Start server thread
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self._running = True

        url = f"http://localhost:{self.port}"
        print(f"Live preview server started: {url}")

        # Open browser
        if self.auto_open:
            time.sleep(0.5)  # Give server time to start
            webbrowser.open(url)

        return self

    def stop(self):
        """Stop the server.

        Alias for shutdown() for backward compatibility.
        """
        self.shutdown()

    def shutdown(self):
        """Shutdown the server gracefully."""
        if not self._running:
            return

        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self._running = False
            print("Live preview server stopped")

        # Clear class-level references
        SSEHandler.patcher = None
        SSEHandler.event_queues.clear()

    def __enter__(self):
        """Context manager entry - server already started in __init__."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - shutdown server."""
        self.shutdown()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Cleanup on deletion."""
        if self._running:
            self.shutdown()

    def notify_update(self):
        """Notify all connected clients of an update."""
        if not self.patcher:
            return

        # Get current state using standalone function
        state = get_patcher_state_json(self.patcher)

        # Send to all connected clients
        with SSEHandler._lock:
            for queue in SSEHandler.event_queues:
                try:
                    queue.put_nowait(state)
                except:
                    pass


def serve_patcher(patcher: 'Patcher', port: int = 8000, auto_open: bool = True) -> PatcherServer:
    """Start a live preview server for a patcher.

    The server can be used as a context manager for automatic cleanup:

        >>> with serve_patcher(p) as server:
        ...     p.add_textbox('cycle~ 440')
        ...     p.save()
        # Server automatically stopped

    Or managed manually:

        >>> server = serve_patcher(p)
        >>> p.add_textbox('cycle~ 440')
        >>> p.save()
        >>> server.shutdown()  # Manual cleanup

    Args:
        patcher: Patcher instance to serve
        port: HTTP server port (default: 8000)
        auto_open: Automatically open browser (default: True)

    Returns:
        PatcherServer instance (context manager)

    Example:
        >>> from py2max import Patcher
        >>> p = Patcher('demo.maxpat')
        >>> with p.serve() as server:
        ...     osc = p.add_textbox('cycle~ 440')
        ...     p.save()  # Updates browser
    """
    server = PatcherServer(patcher, port, auto_open)
    server.start()
    return server


__all__ = ['PatcherServer', 'serve_patcher', 'SSEHandler']
