"""Demonstration of py2max interactive WebSocket editor.

This example shows how to use the interactive WebSocket server for
real-time bidirectional editing of Max patches in the browser.

Usage:
    python examples/interactive_demo.py

Features demonstrated:
    - Interactive WebSocket server
    - Bidirectional communication (Browser ↔ Python)
    - Drag-and-drop object repositioning
    - Connection drawing from browser
    - Object creation from browser
    - Real-time synchronization

Requires:
    - websockets package (pip install websockets)
"""

import asyncio
from py2max import Patcher


async def demo_interactive():
    """Interactive WebSocket editor demonstration."""
    print("=" * 70)
    print("py2max Interactive Editor Demo")
    print("=" * 70)
    print()
    print("This demo starts an interactive WebSocket server that allows")
    print("bidirectional editing between Python and the browser.")
    print()
    print("Features:")
    print("  - Drag objects to reposition them")
    print("  - Double-click canvas to create new objects")
    print("  - Click 'Connect' button, then click two objects to connect them")
    print("  - Press Ctrl+C to stop the server")
    print()

    # Create patcher with some initial objects
    p = Patcher('interactive_demo.maxpat', layout='grid')

    # Add initial objects
    print("Creating initial patch...")
    metro = p.add_textbox('metro 500')
    random_obj = p.add_textbox('random 127')
    mtof = p.add_textbox('mtof')
    osc = p.add_textbox('cycle~')
    gain = p.add_textbox('gain~ 0.5')
    dac = p.add_textbox('ezdac~')

    # Create connections
    p.add_line(metro, random_obj)
    p.add_line(random_obj, mtof)
    p.add_line(mtof, osc)
    p.add_line(osc, gain)
    p.add_line(gain, dac)
    p.add_line(gain, dac, inlet=1)

    # Optimize layout
    p.optimize_layout()

    print("Starting interactive server...")
    print()

    # Import and start interactive server
    from py2max.websocket_server import serve_interactive

    async with await serve_interactive(p, port=8000) as server:
        print()
        print("=" * 70)
        print("Interactive editor is now running!")
        print()
        print("Try these interactions in the browser:")
        print("  1. Drag objects to move them around")
        print("  2. Double-click the canvas to create new objects")
        print("  3. Click 'Connect' button to enable connection mode")
        print("  4. In connection mode, click two objects to connect them")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 70)
        print()

        # Keep server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping server...")


async def demo_interactive_async_updates():
    """Demo showing async Python updates alongside browser edits."""
    print("=" * 70)
    print("py2max Interactive Editor - Async Updates Demo")
    print("=" * 70)
    print()
    print("This demo shows how Python can make updates alongside")
    print("browser interactions, with everything staying in sync.")
    print()

    # Create simple patcher
    p = Patcher('async_demo.maxpat', layout='grid')

    # Add one initial object
    metro = p.add_textbox('metro 1000')
    p.optimize_layout()

    print("Starting interactive server...")
    from py2max.websocket_server import serve_interactive

    server = await serve_interactive(p, port=8001)

    print()
    print("=" * 70)
    print("Server running! Now adding objects from Python...")
    print("=" * 70)
    print()

    try:
        # Add objects periodically from Python while browser is interactive
        for i in range(5):
            await asyncio.sleep(2)
            print(f"Adding object {i+1} from Python...")

            # Add new object
            if i == 0:
                box = p.add_textbox('random 127')
            elif i == 1:
                box = p.add_textbox('mtof')
            elif i == 2:
                box = p.add_textbox('cycle~')
            elif i == 3:
                box = p.add_textbox('gain~ 0.5')
            else:
                box = p.add_textbox('ezdac~')

            # Notify browser of update
            await server.notify_update()

        print()
        print("=" * 70)
        print("All objects added! You can now:")
        print("  - Drag objects to rearrange them")
        print("  - Create connections between them")
        print("  - Add more objects from the browser")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 70)

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        await server.shutdown()


async def demo_context_manager():
    """Demo using async context manager."""
    print("=" * 70)
    print("py2max Interactive Editor - Context Manager Demo")
    print("=" * 70)
    print()

    p = Patcher('context_demo.maxpat', layout='flow')

    # Build a simple synth
    osc = p.add_textbox('cycle~ 440')
    gain = p.add_textbox('gain~ 0.5')
    dac = p.add_textbox('ezdac~')
    p.add_line(osc, gain)
    p.add_line(gain, dac)
    p.optimize_layout()

    print("Starting server with context manager...")
    from py2max.websocket_server import serve_interactive

    async with await serve_interactive(p, port=8002) as server:
        print()
        print("Server running! Edit in browser for 10 seconds...")
        await asyncio.sleep(10)
        print()
        print("Exiting context - server will auto-stop...")

    print()
    print("=" * 70)
    print("Server automatically stopped!")
    print("=" * 70)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == 'async':
            asyncio.run(demo_interactive_async_updates())
        elif mode == 'context':
            asyncio.run(demo_context_manager())
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python examples/interactive_demo.py [async|context]")
    else:
        asyncio.run(demo_interactive())
