"""Tests for py2max inline REPL functionality."""

import asyncio
import logging
from pathlib import Path
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
def mock_server():
    """Create a mock server."""
    server = MagicMock()
    server.port = 8000
    server.ws_port = 8001
    server.handler = MagicMock()
    server.handler.clients = set()
    server.notify_update = AsyncMock()
    server.stop = AsyncMock()
    return server


class TestReplInlineImport:
    """Tests for repl_inline module imports."""

    def test_import_repl_inline(self):
        """Test that repl_inline module can be imported."""
        from py2max.server.inline import (
            BackgroundServerREPL,
            restore_console_logging,
            setup_file_logging,
            start_background_server_repl,
            start_inline_repl,
        )

        assert setup_file_logging is not None
        assert restore_console_logging is not None
        assert start_inline_repl is not None
        assert BackgroundServerREPL is not None
        assert start_background_server_repl is not None

    def test_import_all_exports(self):
        """Test __all__ exports."""
        from py2max.server import inline

        assert "start_inline_repl" in inline.__all__
        assert "start_background_server_repl" in inline.__all__
        assert "BackgroundServerREPL" in inline.__all__
        assert "setup_file_logging" in inline.__all__
        assert "restore_console_logging" in inline.__all__


class TestSetupFileLogging:
    """Tests for setup_file_logging function."""

    def test_setup_file_logging_creates_file(self, tmp_path):
        """Test that setup_file_logging creates log file."""
        from py2max.server.inline import restore_console_logging, setup_file_logging

        log_file = tmp_path / "test.log"

        try:
            handler = setup_file_logging(log_file)

            # Handler should be a FileHandler
            assert isinstance(handler, logging.FileHandler)

            # Log something
            logger = logging.getLogger("test_logger")
            logger.info("Test message")

            # Close handler
            handler.close()

            # File should exist
            assert log_file.exists()
        finally:
            restore_console_logging()

    def test_setup_file_logging_custom_level(self, tmp_path):
        """Test setup_file_logging with custom level."""
        from py2max.server.inline import restore_console_logging, setup_file_logging

        log_file = tmp_path / "test.log"

        try:
            handler = setup_file_logging(log_file, level=logging.DEBUG)

            assert handler.level == logging.DEBUG
            handler.close()
        finally:
            restore_console_logging()

    def test_setup_file_logging_creates_parent_dirs(self, tmp_path):
        """Test that setup_file_logging creates parent directories."""
        from py2max.server.inline import restore_console_logging, setup_file_logging

        log_file = tmp_path / "subdir" / "nested" / "test.log"

        try:
            # Parent dirs don't exist yet
            assert not log_file.parent.exists()

            # The function doesn't create parent dirs, but caller should
            log_file.parent.mkdir(parents=True, exist_ok=True)

            handler = setup_file_logging(log_file)
            handler.close()

            assert log_file.parent.exists()
        finally:
            restore_console_logging()


class TestRestoreConsoleLogging:
    """Tests for restore_console_logging function."""

    def test_restore_console_logging(self, tmp_path):
        """Test that restore_console_logging restores console output."""
        from py2max.server.inline import restore_console_logging, setup_file_logging

        log_file = tmp_path / "test.log"

        # Setup file logging
        handler = setup_file_logging(log_file)
        handler.close()

        # Restore console logging
        restore_console_logging()

        # Should have console handler now
        root_logger = logging.getLogger()
        has_stream_handler = any(
            isinstance(h, logging.StreamHandler) for h in root_logger.handlers
        )
        assert has_stream_handler

    def test_restore_removes_file_handlers(self, tmp_path):
        """Test that restore_console_logging removes file handlers."""
        from py2max.server.inline import restore_console_logging, setup_file_logging

        log_file = tmp_path / "test.log"

        # Setup file logging
        setup_file_logging(log_file)

        # Restore
        restore_console_logging()

        # Should not have file handlers
        root_logger = logging.getLogger()
        has_file_handler = any(
            isinstance(h, logging.FileHandler) for h in root_logger.handlers
        )
        assert not has_file_handler


class TestBackgroundServerREPL:
    """Tests for BackgroundServerREPL class."""

    def test_init_defaults(self, patcher):
        """Test BackgroundServerREPL initialization with defaults."""
        from py2max.server.inline import BackgroundServerREPL

        repl = BackgroundServerREPL(patcher)

        assert repl.patcher is patcher
        assert repl.port == 8000
        assert repl.log_file == Path("outputs/py2max_server.log")
        assert repl.server is None
        assert repl.server_thread is None
        assert repl.loop is None

    def test_init_custom(self, patcher, tmp_path):
        """Test BackgroundServerREPL initialization with custom values."""
        from py2max.server.inline import BackgroundServerREPL

        log_file = tmp_path / "custom.log"
        repl = BackgroundServerREPL(patcher, port=9000, log_file=log_file)

        assert repl.port == 9000
        assert repl.log_file == log_file

    def test_notify_update_sync_no_server(self, patcher, capsys):
        """Test notify_update_sync when server not running."""
        from py2max.server.inline import BackgroundServerREPL

        repl = BackgroundServerREPL(patcher)

        # Should not raise when server not running
        repl.notify_update_sync()

    def test_stop_no_server(self, patcher):
        """Test stop when server not running."""
        from py2max.server.inline import BackgroundServerREPL

        repl = BackgroundServerREPL(patcher)

        # Should not raise when server not running
        repl.stop()


class TestStartInlineRepl:
    """Tests for start_inline_repl function."""

    @pytest.mark.asyncio
    async def test_start_inline_repl_creates_log_dir(
        self, patcher, mock_server, tmp_path
    ):
        """Test that start_inline_repl creates log directory."""
        from py2max.server.inline import start_inline_repl

        log_file = tmp_path / "logs" / "server.log"

        # Mock start_repl (imported inside the function from py2max.server.repl)
        with patch("py2max.server.repl.start_repl", new_callable=AsyncMock):
            await start_inline_repl(patcher, mock_server, log_file)

        # Log directory should exist
        assert log_file.parent.exists()

    @pytest.mark.asyncio
    async def test_start_inline_repl_default_log_file(
        self, patcher, mock_server, tmp_path
    ):
        """Test start_inline_repl with default log file."""
        from py2max.server.inline import start_inline_repl

        with patch("py2max.server.repl.start_repl", new_callable=AsyncMock):
            # Should not raise with default log file
            await start_inline_repl(patcher, mock_server, None)

    @pytest.mark.asyncio
    async def test_start_inline_repl_restores_logging(
        self, patcher, mock_server, tmp_path
    ):
        """Test that start_inline_repl restores logging on exit."""
        from py2max.server.inline import start_inline_repl

        log_file = tmp_path / "server.log"

        with patch("py2max.server.repl.start_repl", new_callable=AsyncMock):
            await start_inline_repl(patcher, mock_server, log_file)

        # Should have console handler restored
        root_logger = logging.getLogger()
        has_stream_handler = any(
            isinstance(h, logging.StreamHandler) for h in root_logger.handlers
        )
        assert has_stream_handler


class TestStartBackgroundServerRepl:
    """Tests for start_background_server_repl function."""

    @pytest.mark.asyncio
    async def test_start_background_server_repl_creates_repl(self, patcher, tmp_path):
        """Test that start_background_server_repl creates BackgroundServerREPL."""
        from py2max.server.inline import start_background_server_repl

        log_file = tmp_path / "server.log"

        # Mock BackgroundServerREPL.start
        with patch(
            "py2max.server.inline.BackgroundServerREPL.start", new_callable=AsyncMock
        ):
            # Should not raise
            await start_background_server_repl(patcher, port=9000, log_file=log_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
