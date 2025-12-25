"""Tests for py2max REPL server functionality."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from py2max import Patcher


@pytest.fixture
def patcher(tmp_path):
    """Create a test patcher."""
    patch_path = tmp_path / "test.maxpat"
    p = Patcher(patch_path, layout="grid")
    return p


@pytest.fixture
def mock_interactive_server():
    """Create a mock InteractivePatcherServer."""
    server = MagicMock()
    server.port = 8000
    server.ws_port = 8001
    server.handler = MagicMock()
    server.handler.clients = set()
    server.notify_update = AsyncMock()
    return server


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.send = AsyncMock()
    ws.recv = AsyncMock()
    ws.close = AsyncMock()
    ws.remote_address = ("127.0.0.1", 54321)
    return ws


class TestReplServerImport:
    """Tests for ReplServer module imports."""

    def test_import_repl_server(self):
        """Test that repl_server module can be imported."""
        from py2max.server.rpc import ReplServer, start_repl_server

        assert ReplServer is not None
        assert start_repl_server is not None

    def test_import_all_exports(self):
        """Test __all__ exports."""
        from py2max.server import rpc

        assert "ReplServer" in rpc.__all__
        assert "start_repl_server" in rpc.__all__


class TestReplServer:
    """Tests for ReplServer class."""

    def test_init(self, patcher, mock_interactive_server):
        """Test ReplServer initialization."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        assert server.patcher is patcher
        assert server.server is mock_interactive_server
        assert len(server.clients) == 0
        assert server.namespace is not None

    def test_namespace_contents(self, patcher, mock_interactive_server):
        """Test ReplServer namespace contains expected objects."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        # Check patcher references
        assert server.namespace["p"] is patcher
        assert server.namespace["patcher"] is patcher
        assert server.namespace["server"] is mock_interactive_server

        # Check command functions
        assert "save" in server.namespace
        assert "info" in server.namespace
        assert "layout" in server.namespace
        assert "optimize" in server.namespace
        assert "clear" in server.namespace
        assert "clients" in server.namespace
        assert "help_obj" in server.namespace
        assert "commands" in server.namespace

    @pytest.mark.asyncio
    async def test_handle_init(self, patcher, mock_interactive_server, mock_websocket):
        """Test handling init message."""
        from py2max.server.rpc import ReplServer

        # Add some objects
        patcher.add_textbox("cycle~ 440")
        patcher.add_textbox("gain~")

        server = ReplServer(patcher, mock_interactive_server)
        await server.handle_init(mock_websocket)

        # Check response was sent
        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)

        assert response["type"] == "init_response"
        assert "info" in response
        assert response["info"]["num_objects"] == 2
        assert response["info"]["num_connections"] == 0

    @pytest.mark.asyncio
    async def test_handle_eval_expression(
        self, patcher, mock_interactive_server, mock_websocket
    ):
        """Test evaluating an expression."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        # Evaluate simple expression
        await server.handle_eval(mock_websocket, {"code": "1 + 1"})

        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)

        assert response["type"] == "result"
        assert response["result"] == "2"

    @pytest.mark.asyncio
    async def test_handle_eval_statement(
        self, patcher, mock_interactive_server, mock_websocket
    ):
        """Test evaluating a statement (exec mode)."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        # Evaluate statement that sets variable
        await server.handle_eval(mock_websocket, {"code": "x = 42"})

        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)

        assert response["type"] == "result"
        # Statement should have None result
        assert response["result"] is None

        # Variable should be in namespace
        assert server.namespace.get("x") == 42

    @pytest.mark.asyncio
    async def test_handle_eval_with_output(
        self, patcher, mock_interactive_server, mock_websocket
    ):
        """Test evaluating code that produces output."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        # Evaluate code with print
        await server.handle_eval(mock_websocket, {"code": "print('hello')"})

        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)

        assert response["type"] == "result"
        assert response["display"] is not None
        assert "hello" in response["display"]

    @pytest.mark.asyncio
    async def test_handle_eval_empty_code(
        self, patcher, mock_interactive_server, mock_websocket
    ):
        """Test evaluating empty code."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        await server.handle_eval(mock_websocket, {"code": ""})

        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)

        assert response["type"] == "result"
        assert response["result"] is None

    @pytest.mark.asyncio
    async def test_handle_eval_error(
        self, patcher, mock_interactive_server, mock_websocket
    ):
        """Test evaluating code that raises error."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        # Evaluate code that raises error
        await server.handle_eval(mock_websocket, {"code": "1/0"})

        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)

        assert response["type"] == "error"
        assert (
            "ZeroDivisionError" in response["error"] or "division" in response["error"]
        )
        assert "traceback" in response

    @pytest.mark.asyncio
    async def test_handle_message_init(
        self, patcher, mock_interactive_server, mock_websocket
    ):
        """Test handle_message with init type."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        await server.handle_message(mock_websocket, json.dumps({"type": "init"}))

        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)

        assert response["type"] == "init_response"

    @pytest.mark.asyncio
    async def test_handle_message_eval(
        self, patcher, mock_interactive_server, mock_websocket
    ):
        """Test handle_message with eval type."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        await server.handle_message(
            mock_websocket, json.dumps({"type": "eval", "code": "2 + 2"})
        )

        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)

        assert response["type"] == "result"
        assert response["result"] == "4"

    @pytest.mark.asyncio
    async def test_handle_message_unknown_type(
        self, patcher, mock_interactive_server, mock_websocket
    ):
        """Test handle_message with unknown type."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        await server.handle_message(
            mock_websocket, json.dumps({"type": "unknown_type"})
        )

        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)

        assert response["type"] == "error"
        assert "Unknown message type" in response["error"]

    @pytest.mark.asyncio
    async def test_handle_message_invalid_json(
        self, patcher, mock_interactive_server, mock_websocket
    ):
        """Test handle_message with invalid JSON."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        await server.handle_message(mock_websocket, "not valid json")

        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)

        assert response["type"] == "error"
        assert "Invalid JSON" in response["error"]

    @pytest.mark.asyncio
    async def test_handle_eval_async_coroutine(
        self, patcher, mock_interactive_server, mock_websocket
    ):
        """Test evaluating async code."""
        from py2max.server.rpc import ReplServer

        server = ReplServer(patcher, mock_interactive_server)

        # Add asyncio to namespace for the test
        await server.handle_eval(mock_websocket, {"code": "asyncio.sleep(0)"})

        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)

        # Should handle coroutine and return result
        assert response["type"] == "result"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
