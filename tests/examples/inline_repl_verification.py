"""Test script for Option 2b: Single-terminal REPL with log redirection.

This script demonstrates that the inline REPL mode can be started
programmatically without CLI interaction.

Usage:
    python tests/examples/test_inline_repl_mode.py
"""

import asyncio
from pathlib import Path


async def test_inline_repl():
    """Test inline REPL startup and basic functionality."""
    from py2max import Patcher
    from py2max.repl_inline import BackgroundServerREPL

    # Create test patch
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    patch_path = output_dir / "test_inline_repl.maxpat"

    print("Creating test patch...")
    p = Patcher(patch_path)
    osc = p.add("cycle~ 440")
    gain = p.add("gain~")
    p.link(osc, gain)
    p.save()

    print("\nTest 1: Verify BackgroundServerREPL can be instantiated")
    log_file = output_dir / "test_server.log"
    repl = BackgroundServerREPL(p, port=8100, log_file=log_file)
    print(f"  ✓ BackgroundServerREPL created")
    print(f"  ✓ Log file: {repl.log_file}")
    print(f"  ✓ Port: {repl.port}")

    print("\nTest 2: Verify log file setup functions exist")
    from py2max.repl_inline import setup_file_logging, restore_console_logging

    print(f"  ✓ setup_file_logging: {setup_file_logging}")
    print(f"  ✓ restore_console_logging: {restore_console_logging}")

    print("\nTest 3: Verify start_background_server_repl function exists")
    from py2max.repl_inline import start_background_server_repl

    print(f"  ✓ start_background_server_repl: {start_background_server_repl}")

    print("\n" + "=" * 70)
    print("All inline REPL components verified!")
    print("=" * 70)
    print()
    print("To test full inline REPL mode, run:")
    print(f"  py2max serve {patch_path} --repl --log-file {log_file}")
    print()
    print("This will:")
    print("  1. Start server in background thread")
    print("  2. Redirect logs to file")
    print("  3. Start REPL in foreground (single terminal)")
    print()


if __name__ == "__main__":
    asyncio.run(test_inline_repl())
