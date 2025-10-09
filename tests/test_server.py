"""Tests for the SSE live preview server."""

import json
import threading
import time
from pathlib import Path

import pytest

from py2max import Patcher
from py2max.server import (
    PatcherServer,
    SSEHandler,
    get_patcher_state_json,
    serve_patcher,
)


class TestGetPatcherStateJson:
    """Tests for the standalone get_patcher_state_json function."""

    def test_empty_patcher(self):
        """Test with empty patcher."""
        p = Patcher('test.maxpat')
        state = get_patcher_state_json(p)

        assert state['type'] == 'update'
        assert state['boxes'] == []
        assert state['lines'] == []
        # Default title is 'Untitled Patch'
        assert 'title' in state

    def test_none_patcher(self):
        """Test with None patcher."""
        state = get_patcher_state_json(None)

        assert state['type'] == 'update'
        assert state['boxes'] == []
        assert state['lines'] == []

    def test_with_boxes(self):
        """Test with boxes."""
        p = Patcher('test.maxpat')
        osc = p.add_textbox('cycle~ 440')
        gain = p.add_textbox('gain~')

        state = get_patcher_state_json(p)

        assert len(state['boxes']) == 2
        assert state['boxes'][0]['text'] == 'cycle~ 440'
        assert state['boxes'][1]['text'] == 'gain~'

    def test_with_lines(self):
        """Test with patchlines."""
        p = Patcher('test.maxpat')
        osc = p.add_textbox('cycle~ 440')
        gain = p.add_textbox('gain~')
        p.add_line(osc, gain)

        state = get_patcher_state_json(p)

        assert len(state['lines']) == 1
        assert state['lines'][0]['src'] == osc.id
        assert state['lines'][0]['dst'] == gain.id
        assert state['lines'][0]['src_outlet'] == 0
        assert state['lines'][0]['dst_inlet'] == 0

    def test_box_position_rect_object(self):
        """Test box position with Rect object."""
        p = Patcher('test.maxpat')
        osc = p.add_textbox('cycle~ 440')

        state = get_patcher_state_json(p)
        box = state['boxes'][0]

        assert 'x' in box
        assert 'y' in box
        assert 'width' in box
        assert 'height' in box

    def test_box_inlet_outlet_counts(self):
        """Test inlet/outlet counts are included."""
        p = Patcher('test.maxpat')
        osc = p.add_textbox('cycle~ 440')

        state = get_patcher_state_json(p)
        box = state['boxes'][0]

        assert 'inlet_count' in box
        assert 'outlet_count' in box
        assert isinstance(box['inlet_count'], int)
        assert isinstance(box['outlet_count'], int)


class TestPatcherServer:
    """Tests for the PatcherServer class."""

    def test_init(self):
        """Test server initialization."""
        p = Patcher('test.maxpat')
        server = PatcherServer(p, port=8001, auto_open=False)

        assert server.patcher is p
        assert server.port == 8001
        assert server.auto_open is False
        assert server._running is False

    def test_start_stop(self):
        """Test starting and stopping the server."""
        p = Patcher('test.maxpat')
        server = PatcherServer(p, port=8002, auto_open=False)

        # Start server
        server.start()
        assert server._running is True
        assert server.server is not None
        assert server.server_thread is not None

        # Give server time to start
        time.sleep(0.1)

        # Stop server
        server.shutdown()
        assert server._running is False

    def test_start_already_running(self, capsys):
        """Test starting server when already running."""
        p = Patcher('test.maxpat')
        server = PatcherServer(p, port=8003, auto_open=False)

        server.start()
        server.start()  # Try to start again

        captured = capsys.readouterr()
        assert "already running" in captured.out.lower()

        server.shutdown()

    def test_stop_not_running(self):
        """Test stopping server when not running."""
        p = Patcher('test.maxpat')
        server = PatcherServer(p, port=8004, auto_open=False)

        # Should not raise error
        server.shutdown()

    def test_stop_alias(self):
        """Test stop() as alias for shutdown()."""
        p = Patcher('test.maxpat')
        server = PatcherServer(p, port=8005, auto_open=False)

        server.start()
        assert server._running is True

        server.stop()  # Use alias
        assert server._running is False

    def test_context_manager(self):
        """Test using server as context manager."""
        p = Patcher('test.maxpat')

        with PatcherServer(p, port=8006, auto_open=False) as server:
            server.start()
            assert server._running is True
            time.sleep(0.1)

        # Server should be stopped after exiting context
        assert server._running is False

    def test_context_manager_with_exception(self):
        """Test context manager handles exceptions properly."""
        p = Patcher('test.maxpat')

        with pytest.raises(ValueError):
            with PatcherServer(p, port=8007, auto_open=False) as server:
                server.start()
                assert server._running is True
                raise ValueError("Test exception")

        # Server should still be stopped
        assert server._running is False

    def test_del_cleanup(self):
        """Test __del__ cleanup."""
        p = Patcher('test.maxpat')
        server = PatcherServer(p, port=8008, auto_open=False)
        server.start()
        time.sleep(0.1)

        # Delete server - should trigger cleanup
        del server
        time.sleep(0.1)

        # Verify cleanup happened (SSEHandler state should be cleared)
        assert SSEHandler.patcher is None

    def test_notify_update(self):
        """Test notify_update sends to all clients."""
        p = Patcher('test.maxpat')
        server = PatcherServer(p, port=8009, auto_open=False)
        server.start()
        time.sleep(0.1)

        # Add a box
        p.add_textbox('cycle~ 440')

        # Notify update (should not raise error even with no clients)
        server.notify_update()

        server.shutdown()

    def test_notify_update_none_patcher(self):
        """Test notify_update with None patcher."""
        server = PatcherServer(None, port=8010, auto_open=False)
        server.start()
        time.sleep(0.1)

        # Should not raise error
        server.notify_update()

        server.shutdown()


class TestServePatcher:
    """Tests for the serve_patcher convenience function."""

    def test_serve_patcher(self):
        """Test serve_patcher function."""
        p = Patcher('test.maxpat')
        server = serve_patcher(p, port=8011, auto_open=False)

        assert isinstance(server, PatcherServer)
        assert server._running is True
        assert server.patcher is p

        server.shutdown()

    def test_serve_patcher_as_context_manager(self):
        """Test serve_patcher result as context manager."""
        p = Patcher('test.maxpat')

        with serve_patcher(p, port=8012, auto_open=False) as server:
            assert server._running is True
            time.sleep(0.1)

        assert server._running is False


class TestPatcherIntegration:
    """Tests for Patcher.serve() integration."""

    def test_patcher_serve(self):
        """Test Patcher.serve() method."""
        p = Patcher('test.maxpat')
        server = p.serve(port=8013, auto_open=False)

        assert isinstance(server, PatcherServer)
        assert server._running is True
        assert hasattr(p, '_live_server')
        assert p._live_server is server

        server.shutdown()

    def test_patcher_save_notifies(self, tmp_path):
        """Test that Patcher.save() notifies live server."""
        output_file = tmp_path / 'test.maxpat'
        p = Patcher(str(output_file))
        server = p.serve(port=8014, auto_open=False)
        time.sleep(0.1)

        # Add box and save
        p.add_textbox('cycle~ 440')
        p.save()  # Should call notify_update

        # Verify file was saved
        assert output_file.exists()

        server.shutdown()

    def test_patcher_save_without_server(self, tmp_path):
        """Test that Patcher.save() works without live server."""
        output_file = tmp_path / 'test.maxpat'
        p = Patcher(str(output_file))

        p.add_textbox('cycle~ 440')
        p.save()  # Should not raise error

        assert output_file.exists()


class TestSSEHandler:
    """Tests for SSEHandler class-level state."""

    def test_class_state_cleared_on_shutdown(self):
        """Test that class-level state is cleared on shutdown."""
        p = Patcher('test.maxpat')
        server = PatcherServer(p, port=8015, auto_open=False)
        server.start()
        time.sleep(0.1)

        # Verify state is set
        assert SSEHandler.patcher is p

        server.shutdown()

        # Verify state is cleared
        assert SSEHandler.patcher is None
        assert len(SSEHandler.event_queues) == 0
