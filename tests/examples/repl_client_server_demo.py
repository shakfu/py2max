"""Demo: Client-Server REPL for py2max.

This example demonstrates the client-server REPL architecture where
the server runs in one terminal (with logs) and the REPL client runs
in a separate terminal (clean, no logs).

Setup:
    Terminal 1 (Server):
    $ python examples/repl_client_server_demo.py server

    Terminal 2 (REPL Client):
    $ python examples/repl_client_server_demo.py client

    Or using CLI:
    Terminal 1: $ py2max serve my-patch.maxpat
    Terminal 2: $ py2max repl localhost:8002

Architecture:
    ┌─────────────────────┐          ┌──────────────────────┐
    │ Terminal 1 (Server) │          │ Terminal 2 (Client)  │
    │                     │          │                      │
    │ HTTP: 8000          │          │ REPL Client          │
    │ WebSocket: 8001     │◄────────►│ Connected to :8002   │
    │ REPL Server: 8002   │ WebSocket│                      │
    │                     │   RPC    │ py2max>>> osc = ...  │
    │ [server logs here]  │          │ [clean, no logs]     │
    └─────────────────────┘          └──────────────────────┘

Benefits:
    - Server logs stay in server terminal
    - REPL stays clean and usable
    - Can have multiple REPL clients
    - Can reconnect if client crashes
"""

import asyncio
import sys
from pathlib import Path


async def run_server():
    """Run the server (Terminal 1)."""
    from py2max import Patcher

    # Create or load patcher
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    patch_path = output_dir / "repl_demo.maxpat"

    if patch_path.exists():
        print(f"Loading existing patch: {patch_path}")
        p = Patcher.from_file(patch_path)
    else:
        print(f"Creating new patch: {patch_path}")
        p = Patcher(patch_path, layout="grid")

        # Add some initial objects
        metro = p.add_textbox("metro 500")
        random_obj = p.add_textbox("random 127")
        p.add_line(metro, random_obj)
        p.optimize_layout()
        p.save()

    print()
    print("=" * 70)
    print("py2max Server (with REPL)")
    print("=" * 70)
    print()

    # Start server with REPL
    server = await p.serve(port=8000, auto_open=True)

    # Start REPL server
    from py2max.server.rpc import start_repl_server

    repl_server = await start_repl_server(p, server, port=8002)

    print()
    print("=" * 70)
    print("Server is running!")
    print()
    print("Ports:")
    print("  HTTP:        http://localhost:8000")
    print("  WebSocket:   ws://localhost:8001")
    print("  REPL Server: localhost:8002")
    print()
    print("In another terminal, connect with:")
    print("  python examples/repl_client_server_demo.py client")
    print("  OR")
    print("  py2max repl localhost:8002")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        repl_server.close()
        await repl_server.wait_closed()
        await server.stop()
        print("Server stopped.")


async def run_client():
    """Run the REPL client (Terminal 2)."""
    from py2max.server.client import start_repl_client

    # Connect to server
    await start_repl_client("localhost", 8002)


def print_usage():
    """Print usage information."""
    print()
    print("=" * 70)
    print("py2max Client-Server REPL Demo")
    print("=" * 70)
    print()
    print("Usage:")
    print()
    print("  Terminal 1 (Server):")
    print("    python examples/repl_client_server_demo.py server")
    print()
    print("  Terminal 2 (Client):")
    print("    python examples/repl_client_server_demo.py client")
    print()
    print("Or using CLI:")
    print()
    print("  Terminal 1: py2max serve my-patch.maxpat")
    print("  Terminal 2: py2max repl localhost:8002")
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        print("Error: Missing argument", file=sys.stderr)
        print(
            "Usage: python examples/repl_client_server_demo.py [server|client]",
            file=sys.stderr,
        )
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == "server":
        print("Starting server...")
        try:
            asyncio.run(run_server())
        except KeyboardInterrupt:
            print("\nServer stopped.")
    elif mode == "client":
        print("Starting REPL client...")
        try:
            asyncio.run(run_client())
        except KeyboardInterrupt:
            print("\nClient disconnected.")
    else:
        print_usage()
        print(f"Error: Unknown mode: {mode}", file=sys.stderr)
        print(
            "Usage: python examples/repl_client_server_demo.py [server|client]",
            file=sys.stderr,
        )
        sys.exit(1)
