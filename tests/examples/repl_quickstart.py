"""Quickstart guide for py2max Interactive REPL.

This example demonstrates how to use the py2max REPL for interactive
patch creation and editing with real-time browser synchronization.

Usage:
    python examples/repl_quickstart.py

    Or use the CLI:
    py2max serve outputs/repl_demo.maxpat --repl

Features demonstrated:
    - Interactive REPL with async support
    - Custom command functions (save, info, layout, etc.)
    - Auto-sync to browser
    - Rich object display
    - Tab completion
    - Command history
"""

import asyncio
from pathlib import Path

from py2max import Patcher


async def main():
    """Run the REPL quickstart demo."""
    # Create output directory
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    # Create a new patcher or load existing one
    patch_path = output_dir / "repl_demo.maxpat"

    if patch_path.exists():
        print(f"Loading existing patch: {patch_path}")
        p = Patcher.from_file(patch_path)
    else:
        print(f"Creating new patch: {patch_path}")
        p = Patcher(patch_path, layout="grid")

        # Add some initial objects to get started
        print("Adding initial objects...")
        metro = p.add_textbox("metro 500")
        random_obj = p.add_textbox("random 127")
        p.add_line(metro, random_obj)
        p.optimize_layout()
        p.save()
        print(f"Created initial patch with {len(p._boxes)} objects")

    # Start server with REPL
    print()
    print("=" * 70)
    print("Starting py2max Interactive Server with REPL")
    print("=" * 70)
    print()

    # Start server
    server = await p.serve(port=8000, auto_open=True)

    # Start REPL
    from py2max.server.repl import start_repl

    print("Starting REPL...")
    print()

    try:
        await start_repl(p, server)
    except (EOFError, KeyboardInterrupt):
        print()
        print("Exiting REPL...")
    finally:
        # Save and stop server
        p.save()
        await server.stop()
        print()
        print("=" * 70)
        print("Server stopped. Goodbye!")
        print("=" * 70)


def print_usage_guide():
    """Print usage guide for the REPL."""
    print()
    print("=" * 70)
    print("py2max REPL Quickstart Guide")
    print("=" * 70)
    print()
    print("BASIC USAGE:")
    print()
    print("  # Add objects")
    print("  >>> osc = p.add('cycle~ 440')")
    print("  >>> gain = p.add('gain~')")
    print("  >>> dac = p.add('ezdac~')")
    print()
    print("  # Create connections")
    print("  >>> p.link(osc, gain)")
    print("  >>> p.link(gain, dac)")
    print("  >>> p.link(gain, dac, inlet=1)")
    print()
    print("  # Save changes")
    print("  >>> save()")
    print()
    print("REPL COMMANDS:")
    print()
    print("  >>> commands()         # Show all available commands")
    print("  >>> info()             # Show patcher stats")
    print("  >>> layout('flow')     # Change layout manager")
    print("  >>> optimize()         # Optimize layout")
    print("  >>> help_obj('cycle~') # Show Max object help")
    print("  >>> clients()          # Show connected browsers")
    print("  >>> clear()            # Clear all objects")
    print()
    print("ASYNC SUPPORT:")
    print()
    print("  >>> await asyncio.sleep(1)  # Top-level await works!")
    print("  >>> await server.notify_update()  # Manually trigger sync")
    print()
    print("TIPS:")
    print()
    print("  - Changes in browser sync back to Python automatically")
    print("  - Use Tab for completion (try typing 'p.add_' and press Tab)")
    print("  - Use Ctrl+R to search command history")
    print("  - Objects display with rich colors (try just typing 'osc')")
    print("  - Press Ctrl+D to exit REPL")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    # Print usage guide first
    print_usage_guide()

    # Run the demo
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
