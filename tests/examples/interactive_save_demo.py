"""
Interactive Save Demo

Demonstrates manual save and optional auto-save functionality.
Web-based edits are persisted to .maxpat files that Max/MSP can read.
"""

import asyncio
import tempfile
from pathlib import Path
from py2max import Patcher
from py2max.websocket_server import serve_interactive


async def manual_save_demo():
    """Demo: Manual save (default behavior)."""

    print("=" * 70)
    print("MANUAL SAVE DEMO")
    print("=" * 70)
    print()

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".maxpat", delete=False) as f:
        temp_path = Path(f.name)

    try:
        # Create initial patch
        p = Patcher(str(temp_path))
        osc = p.add_textbox("cycle~ 440")
        gain = p.add_textbox("gain~ 0.5")
        dac = p.add_textbox("ezdac~")
        p.add_line(osc, gain)
        p.add_line(gain, dac)
        p.save()

        print(f"Created patch: {temp_path}")
        print(f"Objects: {len(p._boxes)}")
        print(f"Connections: {len(p._lines)}")
        print()

        print("Starting interactive server...")
        print("- Auto-save: DISABLED (manual save only)")
        print("- Open browser: http://localhost:8000/")
        print()
        print("Instructions:")
        print("1. Move objects around")
        print("2. Create new objects (double-click or + button)")
        print("3. Create connections (click outlet → click inlet)")
        print("4. Click the 💾 Save button to save changes")
        print("5. Check console for save confirmation")
        print()
        print("Press Ctrl+C to stop server")
        print()

        # Start server with manual save (auto_save=False)
        server = await serve_interactive(p, port=8000, auto_open=True, auto_save=False)

        # Run until interrupted
        try:
            stop_event = asyncio.Event()
            await stop_event.wait()
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n\nStopping server...")
            await server.shutdown()

            # Verify final state
            print("\nFinal state:")
            print(f"Objects: {len(p._boxes)}")
            print(f"Connections: {len(p._lines)}")
            print()

            # Show that Max/MSP can read it
            p2 = Patcher.from_file(str(temp_path))
            print(
                f"Max/MSP can load: {len(p2._boxes)} objects, {len(p2._lines)} connections"
            )
            print()

    finally:
        # Cleanup
        print(f"Cleaning up: {temp_path}")
        temp_path.unlink(missing_ok=True)


async def auto_save_demo():
    """Demo: Auto-save (saves after 2 seconds of no edits)."""

    print("=" * 70)
    print("AUTO-SAVE DEMO")
    print("=" * 70)
    print()

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".maxpat", delete=False) as f:
        temp_path = Path(f.name)

    try:
        # Create initial patch
        p = Patcher(str(temp_path))
        osc = p.add_textbox("cycle~ 440")
        gain = p.add_textbox("gain~ 0.5")
        p.save()

        print(f"Created patch: {temp_path}")
        print(f"Objects: {len(p._boxes)}")
        print()

        print("Starting interactive server...")
        print("- Auto-save: ENABLED (saves 2 seconds after last edit)")
        print("- Open browser: http://localhost:8000/")
        print()
        print("Instructions:")
        print("1. Move objects around")
        print("2. Wait 2 seconds → auto-save triggers")
        print("3. Check console: 'Auto-saved: [filepath]'")
        print("4. Make more edits → waits another 2 seconds")
        print()
        print("Press Ctrl+C to stop server")
        print()

        # Start server with auto-save enabled
        server = await serve_interactive(p, port=8000, auto_open=True, auto_save=True)

        # Run until interrupted
        try:
            stop_event = asyncio.Event()
            await stop_event.wait()
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n\nStopping server...")
            await server.shutdown()

            # Verify final state
            print("\nFinal state:")
            print(f"Objects: {len(p._boxes)}")
            print()

    finally:
        # Cleanup
        print(f"Cleaning up: {temp_path}")
        temp_path.unlink(missing_ok=True)


async def main():
    """Run demos."""

    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        await auto_save_demo()
    else:
        await manual_save_demo()


if __name__ == "__main__":
    print()
    print("Interactive Save Demo")
    print()
    print("Usage:")
    print("  python interactive_save_demo.py       # Manual save (default)")
    print("  python interactive_save_demo.py auto  # Auto-save demo")
    print()

    asyncio.run(main())
