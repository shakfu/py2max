"""Tests for the WebSocket interactive server."""

import asyncio
import pytest

from py2max import Patcher


class TestWebSocketServer:
    """Tests for WebSocket interactive server."""

    @pytest.mark.asyncio
    async def test_import(self):
        """Test that server module can be imported."""
        from py2max.server import (
            InteractiveWebSocketHandler,
            InteractivePatcherServer,
            serve_interactive,
        )

        assert InteractiveWebSocketHandler is not None
        assert InteractivePatcherServer is not None
        assert serve_interactive is not None

    @pytest.mark.asyncio
    async def test_server_init(self):
        """Test server initialization."""
        from py2max.server import InteractivePatcherServer

        p = Patcher("test.maxpat")
        server = InteractivePatcherServer(p, port=9000, auto_open=False)

        assert server.patcher is p
        assert server.port == 9000
        assert server.ws_port == 9001
        assert server.auto_open is False
        assert server._running is False

    @pytest.mark.asyncio
    async def test_server_start_stop(self):
        """Test starting and stopping server."""
        from py2max.server import InteractivePatcherServer

        p = Patcher("test.maxpat")
        server = InteractivePatcherServer(p, port=9002, auto_open=False)

        # Start server
        await server.start()
        assert server._running is True
        assert server.ws_server is not None
        assert server.http_server is not None

        # Give servers time to start
        await asyncio.sleep(0.2)

        # Stop server
        await server.shutdown()
        assert server._running is False

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using server as async context manager."""
        from py2max.server import InteractivePatcherServer

        p = Patcher("test.maxpat")

        async with InteractivePatcherServer(p, port=9003, auto_open=False) as server:
            await server.start()
            assert server._running is True
            await asyncio.sleep(0.1)

        # Server should be stopped after exiting context
        assert server._running is False

    @pytest.mark.asyncio
    async def test_serve_interactive(self):
        """Test serve_interactive convenience function."""
        from py2max.server import serve_interactive

        p = Patcher("test.maxpat")
        server = await serve_interactive(p, port=9004, auto_open=False)

        assert server._running is True
        assert server.patcher is p

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_patcher_serve(self):
        """Test Patcher.serve() method."""
        p = Patcher("test.maxpat")
        server = await p.serve(port=9005, auto_open=False)

        assert server._running is True
        assert hasattr(p, "_server")
        assert p._server is server

        await server.shutdown()

    @pytest.mark.asyncio
    async def test_handler_broadcast(self):
        """Test handler broadcast functionality."""
        from py2max.server import InteractiveWebSocketHandler

        p = Patcher("test.maxpat")
        p.add_textbox("cycle~ 440")

        handler = InteractiveWebSocketHandler(p)

        # Should not raise error with no clients
        await handler.broadcast({"type": "update", "boxes": [], "lines": []})

        assert len(handler.clients) == 0

    @pytest.mark.asyncio
    async def test_notify_update(self):
        """Test notify_update sends updates."""
        from py2max.server import InteractivePatcherServer

        p = Patcher("test.maxpat")
        server = InteractivePatcherServer(p, port=9006, auto_open=False)
        await server.start()

        # Add objects
        p.add_textbox("cycle~ 440")

        # Should not raise error even with no clients
        await server.notify_update()

        await server.shutdown()


class TestWebSocketHandler:
    """Tests for WebSocket handler message processing."""

    @pytest.mark.asyncio
    async def test_handle_update_position(self):
        """Test handling position update message."""
        from py2max.server import InteractiveWebSocketHandler

        p = Patcher("test.maxpat")
        box = p.add_textbox("cycle~ 440")

        handler = InteractiveWebSocketHandler(p)

        # Update position
        await handler.handle_update_position({"box_id": box.id, "x": 100, "y": 200})

        # Check position was updated
        assert box.patching_rect.x == 100
        assert box.patching_rect.y == 200

    @pytest.mark.asyncio
    async def test_handle_create_object(self):
        """Test handling object creation message."""
        from py2max.server import InteractiveWebSocketHandler

        p = Patcher("test.maxpat")
        handler = InteractiveWebSocketHandler(p)

        initial_count = len(p._boxes)

        # Create object
        await handler.handle_create_object({"text": "gain~", "x": 150, "y": 250})

        # Check object was created
        assert len(p._boxes) == initial_count + 1
        new_box = p._boxes[-1]
        assert new_box.text == "gain~"
        assert new_box.patching_rect.x == 150
        assert new_box.patching_rect.y == 250

    @pytest.mark.asyncio
    async def test_handle_create_connection(self):
        """Test handling connection creation message."""
        from py2max.server import InteractiveWebSocketHandler

        p = Patcher("test.maxpat")
        box1 = p.add_textbox("cycle~ 440")
        box2 = p.add_textbox("gain~")

        handler = InteractiveWebSocketHandler(p)

        initial_count = len(p._lines)

        # Create connection
        await handler.handle_create_connection(
            {"src_id": box1.id, "dst_id": box2.id, "src_outlet": 0, "dst_inlet": 0}
        )

        # Check connection was created
        assert len(p._lines) == initial_count + 1
        new_line = p._lines[-1]
        assert new_line.src == box1.id
        assert new_line.dst == box2.id

    @pytest.mark.asyncio
    async def test_handle_delete_object(self):
        """Test handling object deletion message."""
        from py2max.server import InteractiveWebSocketHandler

        p = Patcher("test.maxpat")
        box = p.add_textbox("cycle~ 440")
        box_id = box.id

        handler = InteractiveWebSocketHandler(p)

        # Delete object
        await handler.handle_delete_object({"box_id": box_id})

        # Check object was deleted
        assert len(p._boxes) == 0

    @pytest.mark.asyncio
    async def test_handle_delete_connection(self):
        """Test handling connection deletion message."""
        from py2max.server import InteractiveWebSocketHandler

        p = Patcher("test.maxpat")
        box1 = p.add_textbox("cycle~ 440")
        box2 = p.add_textbox("gain~")
        p.add_line(box1, box2)

        handler = InteractiveWebSocketHandler(p)

        # Delete connection
        await handler.handle_delete_connection(
            {"src_id": box1.id, "dst_id": box2.id, "src_outlet": 0, "dst_inlet": 0}
        )

        # Check connection was deleted
        assert len(p._lines) == 0
