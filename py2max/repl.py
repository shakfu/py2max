"""Interactive REPL for py2max using ptpython.

This module provides an async-aware REPL for interactive patcher editing
with automatic synchronization to the WebSocket server and browser.

Features:
    - Async-aware execution (top-level await)
    - Auto-save and sync after commands
    - Custom command functions (save, info, layout, etc.)
    - Tab completion for Max objects
    - Syntax highlighting
    - Command history
    - Rich object display

Example:
    >>> from py2max import Patcher
    >>> import asyncio
    >>>
    >>> async def main():
    ...     p = Patcher('demo.maxpat')
    ...     server = await p.serve(port=8000)
    ...     await start_repl(p, server)
    >>>
    >>> asyncio.run(main())
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from prompt_toolkit.formatted_text import HTML

if TYPE_CHECKING:
    from .core import Patcher
    from .server import InteractivePatcherServer

# Check if ptpython is available
try:
    from ptpython.repl import embed, run_config
except ImportError:
    raise ImportError(
        "ptpython package required for REPL. "
        "Install with: pip install ptpython or uv add ptpython"
    )


class ReplCommands:
    """Custom command functions for py2max REPL.

    These functions provide IPython-style magic command functionality
    without requiring IPython as a dependency.
    """

    def __init__(self, patcher: "Patcher", server: "InteractivePatcherServer"):
        self.patcher = patcher
        self.server = server

    def save(self) -> None:
        """Save patcher to disk.

        Example:
            >>> save()
            ✓ Saved: demo.maxpat
        """
        if self.patcher.filepath:
            self.patcher.save()
            print(f"✓ Saved: {self.patcher.filepath}")
        else:
            print("⚠ No filepath set - use p.save_as('path.maxpat')")

    def info(self, verbose: bool = False) -> None:
        """Show patcher information.

        Args:
            verbose: If True, show detailed box and connection information

        Example:
            >>> info()
            Patcher: demo.maxpat
            Objects: 5 boxes
            Connections: 4 lines
            Layout: grid (horizontal)
            Server: http://localhost:8000 (1 client)

            >>> info(verbose=True)
            # Shows detailed box and connection information
        """
        filepath = self.patcher.filepath or "Untitled"
        boxes = len(self.patcher._boxes)
        lines = len(self.patcher._lines)
        layout = getattr(self.patcher._layout_mgr, "__class__.__name__", "Unknown")
        clients = len(self.server.handler.clients)

        print()
        print("=" * 70)
        print(f"Patcher: {filepath}")
        print("=" * 70)
        print(f"Objects: {boxes} boxes")
        print(f"Connections: {lines} lines")
        print(f"Layout: {layout}")
        print(f"Server: http://localhost:{self.server.port} ({clients} client{'s' if clients != 1 else ''})")

        if verbose and boxes > 0:
            print()
            print("-" * 70)
            print("BOXES:")
            print("-" * 70)

            for box in self.patcher._boxes:
                box_id = getattr(box, "id", "unknown")
                maxclass = getattr(box, "maxclass", "unknown")
                text = getattr(box, "text", None)
                pos = getattr(box, "patching_rect", None)

                # Format position
                pos_str = ""
                if pos:
                    # Handle both Rect objects and lists
                    if hasattr(pos, 'x'):
                        pos_str = f" @ [{int(pos.x)}, {int(pos.y)}]"
                    elif isinstance(pos, (list, tuple)) and len(pos) >= 2:
                        pos_str = f" @ [{int(pos[0])}, {int(pos[1])}]"

                # Format text/description
                if text:
                    desc = f"{maxclass}: '{text}'"
                else:
                    desc = maxclass

                print(f"  [{box_id}] {desc}{pos_str}")

        if verbose and lines > 0:
            print()
            print("-" * 70)
            print("CONNECTIONS:")
            print("-" * 70)

            for line in self.patcher._lines:
                src = line.source if hasattr(line, "source") else []
                dst = line.destination if hasattr(line, "destination") else []

                if len(src) >= 2 and len(dst) >= 2:
                    src_id = src[0]
                    src_outlet = src[1]
                    dst_id = dst[0]
                    dst_inlet = dst[1]

                    # Try to get box names for better readability
                    src_box = self.patcher._objects.get(src_id)
                    dst_box = self.patcher._objects.get(dst_id)

                    src_name = ""
                    dst_name = ""

                    if src_box:
                        src_text = getattr(src_box, "text", None)
                        if src_text:
                            # Truncate long text
                            src_name = f" ({src_text[:20]}...)" if len(src_text) > 20 else f" ({src_text})"

                    if dst_box:
                        dst_text = getattr(dst_box, "text", None)
                        if dst_text:
                            dst_name = f" ({dst_text[:20]}...)" if len(dst_text) > 20 else f" ({dst_text})"

                    print(f"  [{src_id}]{src_name} outlet {src_outlet} -> [{dst_id}]{dst_name} inlet {dst_inlet}")

        print("=" * 70)
        print()

    def layout(self, layout_type: str = "grid") -> None:
        """Change layout manager.

        Args:
            layout_type: Layout type ('horizontal', 'vertical', 'grid', 'flow',
                        'columnar', 'matrix')

        Example:
            >>> layout('flow')
            ✓ Layout changed to: flow
        """
        try:
            self.patcher.set_layout_mgr(layout_type)
            print(f"✓ Layout changed to: {layout_type}")
        except Exception as e:
            print(f"✗ Error changing layout: {e}")

    def optimize(self) -> None:
        """Optimize layout positioning.

        Example:
            >>> optimize()
            ✓ Layout optimized
        """
        self.patcher.optimize_layout()
        print("✓ Layout optimized")

    def clear(self) -> None:
        """Clear all objects from patcher.

        Example:
            >>> clear()
            ✓ Cleared 5 objects and 4 connections
        """
        boxes = len(self.patcher._boxes)
        lines = len(self.patcher._lines)
        self.patcher._boxes.clear()
        self.patcher._lines.clear()
        self.patcher._objects.clear()
        self.patcher._node_ids.clear()
        self.patcher._edge_ids.clear()
        print(f"✓ Cleared {boxes} objects and {lines} connections")

    def clients(self) -> None:
        """Show connected WebSocket clients.

        Example:
            >>> clients()
            Connected clients: 2
            - Client 1: ws://localhost:8001
            - Client 2: ws://localhost:8001
        """
        client_list = list(self.server.handler.clients)
        count = len(client_list)
        print(f"Connected clients: {count}")
        if count > 0:
            for i, client in enumerate(client_list, 1):
                # Get client info if available
                remote = getattr(client, "remote_address", ("unknown", "unknown"))
                print(f"  - Client {i}: {remote[0]}:{remote[1]}")

    def help_obj(self, obj_name: Optional[str] = None) -> None:
        """Show Max object help.

        Args:
            obj_name: Max object name (e.g., 'cycle~', 'gain~')

        Example:
            >>> help_obj('cycle~')
            cycle~: Sinusoidal oscillator
            ...
        """
        if not obj_name:
            print("Usage: help_obj('object_name')")
            print("Example: help_obj('cycle~')")
            return

        try:
            from .maxref import get_object_help

            help_text = get_object_help(obj_name)
            if help_text:
                print(help_text)
            else:
                print(f"⚠ No help found for: {obj_name}")
        except Exception as e:
            print(f"✗ Error getting help: {e}")

    def commands(self) -> None:
        """Show available REPL commands.

        Example:
            >>> commands()
            Available commands:
            ...
        """
        print()
        print("=" * 70)
        print("Available commands:")
        print("=" * 70)
        print()
        print("Objects:")
        print("  p              - Patcher object")
        print("  server         - WebSocket server object")
        print()
        print("Commands:")
        print("  save()              - Save patcher to disk")
        print("  info(verbose=False) - Show patcher information")
        print("                        Use info(True) for detailed box/connection list")
        print("  layout(type)        - Change layout manager")
        print("  optimize()          - Optimize layout positioning")
        print("  clear()             - Clear all objects")
        print("  clients()           - Show connected WebSocket clients")
        print("  help_obj(name)      - Show Max object help")
        print("  commands()          - Show this help")
        print()
        print("Examples:")
        print("  >>> osc = p.add('cycle~ 440')")
        print("  >>> gain = p.add('gain~')")
        print("  >>> p.link(osc, gain)")
        print("  >>> info()          # Quick summary")
        print("  >>> info(True)      # Detailed view with boxes and connections")
        print("  >>> save()")
        print("=" * 70)
        print()


async def start_repl(
    patcher: "Patcher",
    server: "InteractivePatcherServer",
    title: Optional[str] = None,
) -> None:
    """Start ptpython REPL with py2max context.

    This function starts an async-aware REPL with the patcher and server
    available in the namespace, along with custom command functions.

    Args:
        patcher: Patcher instance to interact with
        server: WebSocket server instance
        title: Optional custom title for the REPL

    Example:
        >>> from py2max import Patcher
        >>> import asyncio
        >>>
        >>> async def main():
        ...     p = Patcher('demo.maxpat')
        ...     server = await p.serve(port=8000)
        ...     await start_repl(p, server)
        >>>
        >>> asyncio.run(main())
    """
    # Create command helper
    commands = ReplCommands(patcher, server)

    # Build namespace with patcher, server, and command functions
    namespace: Dict[str, Any] = {
        # Core objects
        "p": patcher,
        "patcher": patcher,
        "server": server,
        "asyncio": asyncio,
        # Command functions
        "save": commands.save,
        "info": commands.info,
        "layout": commands.layout,
        "optimize": commands.optimize,
        "clear": commands.clear,
        "clients": commands.clients,
        "help_obj": commands.help_obj,
        "commands": commands.commands,
    }

    # Configure ptpython
    def configure(repl):
        """Configure ptpython REPL settings."""
        # Enable features
        repl.show_signature = True
        repl.enable_auto_suggest = True
        repl.show_docstring = True
        repl.complete_while_typing = True
        repl.enable_history_search = True

        # Vi mode (set to False for Emacs mode)
        repl.vi_mode = False

        # Highlighting
        repl.enable_syntax_highlighting = True
        repl.highlight_matching_parenthesis = True

        # History
        repl.enable_system_bindings = True
        repl.enable_open_in_editor = True

        # Mouse support
        repl.enable_mouse_support = True

    # Build title
    if title is None:
        filepath = patcher.filepath or "Untitled"
        if isinstance(filepath, Path):
            filepath = filepath.name
        title = f"py2max - {filepath}"

    # Print banner
    print("=" * 70)
    print("py2max Interactive REPL")
    print("=" * 70)
    print()
    print(f"Patcher: {patcher.filepath or 'Untitled'}")
    print(f"Server: http://localhost:{server.port}")
    print(f"WebSocket: ws://localhost:{server.ws_port}")
    print()
    print("Type 'commands()' to see available commands")
    print("Type 'help(p)' to see patcher API")
    print("Press Ctrl+D or type 'exit()' to quit")
    print()
    print("=" * 70)
    print()

    # Start REPL
    try:
        await embed(
            globals=namespace,
            return_asyncio_coroutine=True,
            patch_stdout=True,
            configure=configure,
            title=title,
        )
    except EOFError:
        # User pressed Ctrl+D
        print()
        print("Exiting REPL...")
    except KeyboardInterrupt:
        # User pressed Ctrl+C
        print()
        print("Interrupted. Use Ctrl+D or exit() to quit.")
        # Continue REPL
        await start_repl(patcher, server, title)
    except Exception as e:
        # Handle ReplExit from exit() command
        if e.__class__.__name__ == "ReplExit":
            print()
            print("Exiting REPL...")
        else:
            raise


class AutoSyncWrapper:
    """Wrapper that auto-saves and syncs after patcher operations.

    This wrapper intercepts calls to patcher methods and automatically
    saves the patcher and notifies WebSocket clients after each operation.

    Note: Currently not used - implemented for potential future use.
    Users can call save() explicitly or we can add auto-sync later.
    """

    def __init__(self, patcher: "Patcher", server: "InteractivePatcherServer"):
        self._patcher = patcher
        self._server = server

    async def _sync(self):
        """Save and notify clients."""
        self._patcher.save()
        await self._server.notify_update()

    def __getattr__(self, name):
        """Intercept attribute access and wrap methods."""
        attr = getattr(self._patcher, name)

        if callable(attr):

            async def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                await self._sync()
                return result

            return wrapper
        return attr


async def start_repl_with_refresh(
    patcher: "Patcher",
    server: "InteractivePatcherServer",
    refresh_callback,
    title: Optional[str] = None,
) -> None:
    """Start ptpython REPL with refresh() function (for single-terminal mode).

    This version adds a refresh() command that can be called manually
    to update the browser view.

    Args:
        patcher: Patcher instance to interact with
        server: WebSocket server instance
        refresh_callback: Callable to notify server of updates
        title: Optional custom title for the REPL

    Example:
        >>> def notify_sync():
        ...     # Notify server in background thread
        ...     pass
        >>> await start_repl_with_refresh(p, server, notify_sync)
    """
    # Create command helper
    commands = ReplCommands(patcher, server)

    # Build namespace with refresh function
    namespace: Dict[str, Any] = {
        # Core objects
        "p": patcher,
        "patcher": patcher,
        "server": server,
        "asyncio": asyncio,
        # Command functions
        "save": commands.save,
        "info": commands.info,
        "layout": commands.layout,
        "optimize": commands.optimize,
        "clear": commands.clear,
        "clients": commands.clients,
        "help_obj": commands.help_obj,
        "commands": commands.commands,
        # Refresh function for single-terminal mode
        "refresh": refresh_callback,
    }

    # Configure ptpython
    def configure(repl):
        """Configure ptpython REPL."""
        # Enable auto-completion
        repl.enable_auto_suggest = True
        repl.complete_while_typing = True

        # Enable syntax highlighting
        repl.enable_syntax_highlighting = True

        # Show signature
        repl.show_signature = True

        # Vi mode (optional - can be toggled with F4)
        repl.vi_mode = False

    # Set title
    if title is None:
        filepath = patcher.filepath or "Untitled"
        title = f"py2max[{filepath}]"

    # Start REPL
    try:
        await embed(
            globals=namespace,
            return_asyncio_coroutine=True,
            configure=configure,
            title=title,
        )
    except EOFError:
        # User pressed Ctrl+D
        print()
        print("Exiting REPL...")
    except KeyboardInterrupt:
        # User pressed Ctrl+C
        print()
        print("Interrupted. Use Ctrl+D or exit() to quit.")
        # Continue REPL
        await start_repl_with_refresh(patcher, server, refresh_callback, title)
    except Exception as e:
        # Handle ReplExit from exit() command
        if e.__class__.__name__ == "ReplExit":
            print()
            print("Exiting REPL...")
        else:
            raise


__all__ = ["start_repl", "start_repl_with_refresh", "ReplCommands", "AutoSyncWrapper"]
