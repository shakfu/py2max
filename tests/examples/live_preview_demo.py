"""Demonstration of py2max live preview server with SSE.

This example shows how to use the live preview server to see patches
update in real-time as you build them in Python.

Usage:
    python examples/live_preview_demo.py
    python examples/live_preview_demo.py interactive
    python examples/live_preview_demo.py context

Features demonstrated:
    - Starting a live preview server
    - Real-time updates as objects are added
    - Automatic browser opening
    - Server-Sent Events (SSE) for one-way communication
    - Context manager for automatic cleanup
"""

from py2max import Patcher
import time


def demo_basic_live_preview():
    """Basic live preview demonstration."""
    print("=" * 70)
    print("py2max Live Preview Demo - Basic")
    print("=" * 70)
    print()

    # Create a patcher and start live server
    print("1. Creating patcher and starting live preview server...")
    p = Patcher("live_demo.maxpat", layout="grid")

    # Start server (opens browser automatically)
    server = p.serve(port=8000)
    print(f"   Server started at: http://localhost:8000")
    print(f"   Browser should have opened automatically")
    print()

    # Give browser time to open
    time.sleep(2)

    # Add objects with delays to see live updates
    print("2. Adding objects (watch the browser update in real-time)...")

    print("   Adding metro...")
    metro = p.add_textbox("metro 500")
    p.save()  # Triggers update
    time.sleep(1)

    print("   Adding cycle~...")
    osc = p.add_textbox("cycle~ 440")
    p.save()
    time.sleep(1)

    print("   Adding gain~...")
    gain = p.add_textbox("gain~ 0.5")
    p.save()
    time.sleep(1)

    print("   Adding ezdac~...")
    dac = p.add_textbox("ezdac~")
    p.save()
    time.sleep(1)

    # Add connections
    print()
    print("3. Adding connections...")

    print("   Connecting metro -> cycle~...")
    p.add_line(metro, osc)
    p.save()
    time.sleep(1)

    print("   Connecting cycle~ -> gain~...")
    p.add_line(osc, gain)
    p.save()
    time.sleep(1)

    print("   Connecting gain~ -> ezdac~...")
    p.add_line(gain, dac)
    p.add_line(gain, dac, inlet=1)
    p.save()
    time.sleep(1)

    # Optimize layout
    print()
    print("4. Optimizing layout...")
    p.optimize_layout()
    p.save()
    time.sleep(2)

    print()
    print("=" * 70)
    print("Demo complete! The patch is visible in your browser.")
    print("The server will continue running. Press Ctrl+C to stop.")
    print("=" * 70)

    # Keep server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()


def demo_interactive_repl():
    """Interactive REPL demonstration."""
    print("=" * 70)
    print("py2max Live Preview - Interactive REPL Mode")
    print("=" * 70)
    print()
    print("This mode lets you interact with the patcher in real-time.")
    print("Try running commands in the Python REPL while watching the browser:")
    print()
    print("  >>> osc2 = p.add_textbox('saw~ 220')")
    print("  >>> p.save()  # Browser updates!")
    print()
    print("Starting server...")
    print()

    # Create patcher and start server
    p = Patcher("interactive_demo.maxpat", layout="flow", flow_direction="vertical")
    server = p.serve(port=8001)

    # Add initial objects
    metro = p.add_textbox("metro 1000")
    random_obj = p.add_textbox("random 127")
    p.add_line(metro, random_obj)
    p.save()

    print("Initial patch created with metro and random.")
    print()
    print("Server running at: http://localhost:8001")
    print()
    print("Try these commands in the Python REPL:")
    print("  >>> mtof = p.add_textbox('mtof')")
    print("  >>> p.add_line(random_obj, mtof)")
    print("  >>> p.save()")
    print()
    print("  >>> osc = p.add_textbox('cycle~')")
    print("  >>> p.add_line(mtof, osc)")
    print("  >>> p.save()")
    print()
    print("Press Ctrl+C to stop the server.")
    print()

    # Keep server running and make objects available
    import code

    code.interact(
        banner="",
        local={"p": p, "server": server, "metro": metro, "random_obj": random_obj},
    )


def demo_context_manager():
    """Demonstration of context manager for automatic cleanup."""
    print("=" * 70)
    print("py2max Live Preview - Context Manager Demo")
    print("=" * 70)
    print()
    print("This demo shows how to use the server as a context manager")
    print("for automatic cleanup when the context exits.")
    print()

    p = Patcher("context_demo.maxpat", layout="grid")

    print("1. Using context manager for automatic cleanup...")
    print()

    # Use server as context manager (auto_open=False to avoid browser in automated tests)
    with p.serve(port=8002, auto_open=False) as server:
        print(f"   Server started at: http://localhost:8002")
        print("   Building patch...")
        time.sleep(0.2)

        # Build a simple patch
        osc = p.add_textbox("cycle~ 440")
        p.save()
        time.sleep(0.2)

        gain = p.add_textbox("gain~ 0.5")
        p.save()
        time.sleep(0.2)

        dac = p.add_textbox("ezdac~")
        p.save()
        time.sleep(0.2)

        p.add_line(osc, gain)
        p.add_line(gain, dac)
        p.save()
        time.sleep(0.2)

        p.optimize_layout()
        p.save()
        time.sleep(0.2)

        print()
        print("   Patch complete! Exiting context...")

    # Server is automatically stopped here
    print()
    print("=" * 70)
    print("Context exited - server automatically stopped!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "interactive":
            demo_interactive_repl()
        elif mode == "context":
            demo_context_manager()
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python examples/live_preview_demo.py [interactive|context]")
    else:
        demo_basic_live_preview()
