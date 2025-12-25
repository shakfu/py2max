"""Tests for py2max REPL functionality."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from py2max import Patcher
from py2max.server.repl import ReplCommands


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
    return server


@pytest.fixture
def repl_commands(patcher, mock_server):
    """Create ReplCommands instance."""
    return ReplCommands(patcher, mock_server)


class TestReplCommands:
    """Tests for ReplCommands class."""

    def test_save_command(self, repl_commands, patcher, capsys):
        """Test save() command."""
        # Save should work when filepath is set
        repl_commands.save()
        captured = capsys.readouterr()
        assert "Saved" in captured.out
        assert str(patcher.filepath) in captured.out

    def test_save_command_no_filepath(self, repl_commands, capsys):
        """Test save() with no filepath."""
        repl_commands.patcher._path = None  # filepath is a property, set _path instead
        repl_commands.save()
        captured = capsys.readouterr()
        assert "No filepath set" in captured.out

    def test_info_command(self, repl_commands, patcher, capsys):
        """Test info() command."""
        # Add some objects
        patcher.add_textbox("cycle~ 440")
        patcher.add_textbox("gain~")

        repl_commands.info()
        captured = capsys.readouterr()

        assert "Patcher:" in captured.out
        assert "Objects: 2 boxes" in captured.out
        assert "Connections: 0 lines" in captured.out
        assert "Server:" in captured.out

    def test_info_command_verbose(self, repl_commands, patcher, capsys):
        """Test info(verbose=True) command with detailed output."""
        # Add some objects
        osc = patcher.add_textbox("cycle~ 440")
        gain = patcher.add_textbox("gain~")
        patcher.link(osc, gain)

        repl_commands.info(verbose=True)
        captured = capsys.readouterr()

        # Check summary
        assert "Patcher:" in captured.out
        assert "Objects: 2 boxes" in captured.out
        assert "Connections: 1 lines" in captured.out

        # Check boxes section
        assert "BOXES:" in captured.out
        assert "cycle~ 440" in captured.out
        assert "gain~" in captured.out

        # Check connections section
        assert "CONNECTIONS:" in captured.out
        assert "outlet" in captured.out
        assert "inlet" in captured.out

    def test_info_command_verbose_with_list_rect(self, repl_commands, patcher, capsys):
        """Test info(verbose=True) with list-based patching_rect (from loaded files)."""
        from py2max.core import Box

        # Create a box with list-based patching_rect (as from JSON files)
        box = Box(
            maxclass="newobj",
            text="metro 500",
            id="test-metro",
            patching_rect=[100, 200, 60, 22],  # List instead of Rect
        )
        patcher._boxes.append(box)
        patcher._objects["test-metro"] = box

        repl_commands.info(verbose=True)
        captured = capsys.readouterr()

        # Should handle list-based rect without error
        assert "BOXES:" in captured.out
        assert "metro 500" in captured.out
        assert "@ [100, 200]" in captured.out  # Should show position from list

    def test_layout_command(self, repl_commands, patcher, capsys):
        """Test layout() command."""
        repl_commands.layout("flow")
        captured = capsys.readouterr()
        assert "Layout changed to: flow" in captured.out

    def test_layout_command_invalid(self, repl_commands, capsys):
        """Test layout() with invalid layout type."""
        repl_commands.layout("invalid")
        captured = capsys.readouterr()
        assert "Error changing layout" in captured.out

    def test_optimize_command(self, repl_commands, patcher, capsys):
        """Test optimize() command."""
        patcher.add_textbox("cycle~ 440")
        patcher.add_textbox("gain~")

        repl_commands.optimize()
        captured = capsys.readouterr()
        assert "Layout optimized" in captured.out

    def test_clear_command(self, repl_commands, patcher, capsys):
        """Test clear() command."""
        # Add some objects and connections
        osc = patcher.add_textbox("cycle~ 440")
        gain = patcher.add_textbox("gain~")
        patcher.add_line(osc, gain)

        assert len(patcher._boxes) == 2
        assert len(patcher._lines) == 1

        repl_commands.clear()

        assert len(patcher._boxes) == 0
        assert len(patcher._lines) == 0

        captured = capsys.readouterr()
        assert "Cleared 2 objects and 1 connections" in captured.out

    def test_clients_command_no_clients(self, repl_commands, capsys):
        """Test clients() with no connected clients."""
        repl_commands.clients()
        captured = capsys.readouterr()
        assert "Connected clients: 0" in captured.out

    def test_clients_command_with_clients(self, repl_commands, mock_server, capsys):
        """Test clients() with connected clients."""
        # Mock clients
        mock_client = MagicMock()
        mock_client.remote_address = ("127.0.0.1", 54321)
        mock_server.handler.clients = {mock_client}

        repl_commands.clients()
        captured = capsys.readouterr()

        assert "Connected clients: 1" in captured.out
        assert "127.0.0.1:54321" in captured.out

    def test_help_obj_command_no_arg(self, repl_commands, capsys):
        """Test help_obj() with no argument."""
        repl_commands.help_obj()
        captured = capsys.readouterr()
        assert "Usage:" in captured.out

    def test_help_obj_command_with_arg(self, repl_commands, capsys):
        """Test help_obj() with Max object name."""
        with patch("py2max.maxref.get_object_help") as mock_help:
            mock_help.return_value = "cycle~: Sinusoidal oscillator"

            repl_commands.help_obj("cycle~")
            captured = capsys.readouterr()

            assert "Sinusoidal oscillator" in captured.out
            mock_help.assert_called_once_with("cycle~")

    def test_help_obj_command_not_found(self, repl_commands, capsys):
        """Test help_obj() with unknown object."""
        with patch("py2max.maxref.get_object_help") as mock_help:
            mock_help.return_value = None

            repl_commands.help_obj("unknown~")
            captured = capsys.readouterr()

            assert "No help found for: unknown~" in captured.out

    def test_commands_command(self, repl_commands, capsys):
        """Test commands() command."""
        repl_commands.commands()
        captured = capsys.readouterr()

        assert "Available commands:" in captured.out
        assert "save()" in captured.out
        assert "info()" in captured.out
        assert "layout(type)" in captured.out


class TestBoxPtRepr:
    """Tests for Box.__pt_repr__ method."""

    def test_box_pt_repr_with_text(self, patcher):
        """Test __pt_repr__ with text content."""
        box = patcher.add_textbox("cycle~ 440")

        # Get HTML representation
        repr_html = box.__pt_repr__()

        # Should contain object type, ID, and text
        assert "newobj" in str(repr_html) or "cycle~" in str(repr_html)

    def test_box_pt_repr_without_text(self, patcher):
        """Test __pt_repr__ without text content."""
        from py2max.core import Box

        box = Box(maxclass="flonum", id="obj-1")

        # Get HTML representation
        repr_html = box.__pt_repr__()

        # Should contain object type and ID
        assert "flonum" in str(repr_html)


@pytest.mark.asyncio
class TestReplIntegration:
    """Integration tests for REPL."""

    async def test_start_repl_basic(self, patcher, mock_server):
        """Test basic REPL startup."""
        # Mock embed function to raise EOFError immediately (simulate Ctrl+D)
        with patch("py2max.server.repl.embed") as mock_embed:
            mock_embed.side_effect = EOFError()

            from py2max.server.repl import start_repl

            # This should not raise (EOFError is caught)
            await start_repl(patcher, mock_server)

            # Verify embed was called with correct parameters
            mock_embed.assert_called_once()
            call_kwargs = mock_embed.call_args[1]

            assert "globals" in call_kwargs
            assert "return_asyncio_coroutine" in call_kwargs
            assert "patch_stdout" in call_kwargs
            assert call_kwargs["return_asyncio_coroutine"] is True
            assert call_kwargs["patch_stdout"] is True

            # Verify namespace contains expected objects
            namespace = call_kwargs["globals"]
            assert "p" in namespace
            assert "patcher" in namespace
            assert "server" in namespace
            assert "save" in namespace
            assert "info" in namespace
            assert namespace["p"] is patcher
            assert namespace["server"] is mock_server

    async def test_start_repl_with_custom_title(self, patcher, mock_server):
        """Test REPL with custom title."""
        with patch("py2max.server.repl.embed") as mock_embed:
            mock_embed.side_effect = EOFError()

            from py2max.server.repl import start_repl

            await start_repl(patcher, mock_server, title="Custom Title")

            call_kwargs = mock_embed.call_args[1]
            assert call_kwargs["title"] == "Custom Title"


class TestAutoSyncWrapper:
    """Tests for AutoSyncWrapper (if implemented)."""

    def test_autosync_wrapper_exists(self):
        """Test that AutoSyncWrapper exists."""
        from py2max.server.repl import AutoSyncWrapper

        assert AutoSyncWrapper is not None

    def test_autosync_wrapper_basic(self, patcher, mock_server):
        """Test AutoSyncWrapper basic functionality."""
        from py2max.server.repl import AutoSyncWrapper

        wrapper = AutoSyncWrapper(patcher, mock_server)

        # Should be able to access patcher attributes
        assert wrapper._patcher is patcher
        assert wrapper._server is mock_server


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
