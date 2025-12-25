"""Tests for py2max REPL client functionality."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestReplClientImport:
    """Tests for ReplClient module imports."""

    def test_import_repl_client(self):
        """Test that repl_client module can be imported."""
        from py2max.repl_client import ReplClient, start_repl_client

        assert ReplClient is not None
        assert start_repl_client is not None

    def test_import_all_exports(self):
        """Test __all__ exports."""
        from py2max import repl_client

        assert "ReplClient" in repl_client.__all__
        assert "start_repl_client" in repl_client.__all__


class TestReplClient:
    """Tests for ReplClient class."""

    def test_init_defaults(self):
        """Test ReplClient initialization with defaults."""
        from py2max.repl_client import ReplClient

        client = ReplClient()

        assert client.host == "localhost"
        assert client.port == 9000
        assert client.ws is None
        assert client.namespace == {}
        assert client.connected is False

    def test_init_custom(self):
        """Test ReplClient initialization with custom values."""
        from py2max.repl_client import ReplClient

        client = ReplClient(host="192.168.1.1", port=8888)

        assert client.host == "192.168.1.1"
        assert client.port == 8888

    @pytest.mark.asyncio
    async def test_execute_not_connected(self, capsys):
        """Test execute when not connected."""
        from py2max.repl_client import ReplClient

        client = ReplClient()
        result = await client.execute("1 + 1")

        assert result is None
        captured = capsys.readouterr()
        assert "Not connected" in captured.err

    @pytest.mark.asyncio
    async def test_execute_with_result(self):
        """Test execute with successful result."""
        from py2max.repl_client import ReplClient

        client = ReplClient()
        client.connected = True

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps({"type": "result", "result": "42", "display": None})
        )
        client.ws = mock_ws

        result = await client.execute("21 * 2")

        assert result == "42"
        mock_ws.send.assert_called_once()
        # Verify sent message
        sent_msg = json.loads(mock_ws.send.call_args[0][0])
        assert sent_msg["type"] == "eval"
        assert sent_msg["code"] == "21 * 2"

    @pytest.mark.asyncio
    async def test_execute_with_display(self, capsys):
        """Test execute with display output."""
        from py2max.repl_client import ReplClient

        client = ReplClient()
        client.connected = True

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps(
                {"type": "result", "result": None, "display": "Hello, World!"}
            )
        )
        client.ws = mock_ws

        result = await client.execute("print('Hello, World!')")

        captured = capsys.readouterr()
        assert "Hello, World!" in captured.out

    @pytest.mark.asyncio
    async def test_execute_with_error(self, capsys):
        """Test execute with error response."""
        from py2max.repl_client import ReplClient

        client = ReplClient()
        client.connected = True

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps(
                {
                    "type": "error",
                    "error": "NameError: name 'undefined' is not defined",
                    "traceback": "Traceback...",
                }
            )
        )
        client.ws = mock_ws

        result = await client.execute("undefined")

        assert result is None
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "undefined" in captured.err

    @pytest.mark.asyncio
    async def test_execute_unknown_response(self, capsys):
        """Test execute with unknown response type."""
        from py2max.repl_client import ReplClient

        client = ReplClient()
        client.connected = True

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps({"type": "unknown", "data": "test"})
        )
        client.ws = mock_ws

        result = await client.execute("test")

        assert result is None
        captured = capsys.readouterr()
        assert "Unknown response type" in captured.err

    @pytest.mark.asyncio
    async def test_execute_exception(self, capsys):
        """Test execute when exception occurs."""
        from py2max.repl_client import ReplClient

        client = ReplClient()
        client.connected = True

        # Mock WebSocket that raises exception
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock(side_effect=Exception("Connection lost"))
        client.ws = mock_ws

        result = await client.execute("test")

        assert result is None
        captured = capsys.readouterr()
        assert "Error executing code" in captured.err

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test disconnect method."""
        from py2max.repl_client import ReplClient

        client = ReplClient()
        client.connected = True

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.close = AsyncMock()
        client.ws = mock_ws

        await client.disconnect()

        mock_ws.close.assert_called_once()
        assert client.connected is False

    @pytest.mark.asyncio
    async def test_disconnect_no_connection(self):
        """Test disconnect when no connection."""
        from py2max.repl_client import ReplClient

        client = ReplClient()

        # Should not raise
        await client.disconnect()
        assert client.connected is False

    @pytest.mark.asyncio
    async def test_connect_success(self, capsys):
        """Test successful connection."""
        from py2max.repl_client import ReplClient

        client = ReplClient()

        # Mock the connect function and websocket
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps(
                {
                    "type": "init_response",
                    "info": {
                        "patcher_path": "test.maxpat",
                        "num_objects": 5,
                        "num_connections": 3,
                    },
                }
            )
        )

        # connect() is an async function that returns a websocket directly
        async def mock_connect(uri):
            return mock_ws

        with patch("py2max.server.client.connect", side_effect=mock_connect):
            await client.connect()

        assert client.connected is True
        assert client.ws is mock_ws

        captured = capsys.readouterr()
        assert "Connected to:" in captured.out
        assert "test.maxpat" in captured.out
        assert "5 boxes" in captured.out
        assert "3 lines" in captured.out

    @pytest.mark.asyncio
    async def test_connect_failure(self, capsys):
        """Test connection failure."""
        from py2max.repl_client import ReplClient

        client = ReplClient()

        with patch(
            "py2max.server.client.connect", side_effect=Exception("Connection refused")
        ):
            with pytest.raises(Exception, match="Connection refused"):
                await client.connect()

        assert client.connected is False
        captured = capsys.readouterr()
        assert "Error connecting" in captured.err


class TestStartReplClient:
    """Tests for start_repl_client function."""

    @pytest.mark.asyncio
    async def test_start_repl_client_connection_error(self, capsys):
        """Test start_repl_client with connection error."""
        from py2max.repl_client import start_repl_client

        with patch(
            "py2max.server.client.connect", side_effect=Exception("Connection refused")
        ):
            result = await start_repl_client("localhost", 9000)

        assert result == 1
        captured = capsys.readouterr()
        assert "error" in captured.err.lower()

    @pytest.mark.asyncio
    async def test_start_repl_client_success(self):
        """Test start_repl_client successful run."""
        from py2max.repl_client import start_repl_client

        # Mock connect and run_repl
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps(
                {
                    "type": "init_response",
                    "info": {
                        "patcher_path": "test.maxpat",
                        "num_objects": 0,
                        "num_connections": 0,
                    },
                }
            )
        )
        mock_ws.close = AsyncMock()

        async def mock_connect(uri):
            return mock_ws

        with patch("py2max.server.client.connect", side_effect=mock_connect):
            with patch(
                "py2max.server.client.ReplClient.run_repl", new_callable=AsyncMock
            ):
                result = await start_repl_client("localhost", 9000)

        assert result == 0


class TestRemoteEvaluator:
    """Tests for RemoteEvaluator class in ReplClient."""

    @pytest.mark.asyncio
    async def test_remote_evaluator_empty_code(self):
        """Test RemoteEvaluator with empty code."""
        from py2max.repl_client import ReplClient

        client = ReplClient()
        client.connected = True

        # Access the _ptpython_repl method to get RemoteEvaluator behavior
        # (testing the class logic indirectly)
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(
            return_value=json.dumps({"type": "result", "result": None, "display": None})
        )
        client.ws = mock_ws

        # Execute empty code
        result = await client.execute("")

        # Empty code should still go through but return None
        # (the check is at the server level for empty strings)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
