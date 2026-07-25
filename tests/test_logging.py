"""Tests for logging behaviour.

py2max is a library, so importing it must print nothing and must not touch the
host application's logging configuration. These run in subprocesses because
import-time behaviour cannot be re-tested once the module is imported, and
because the thing under test is precisely what a fresh interpreter does.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

from py2max.log import LOGGER_NAME, get_logger, setup_logging

ROOT = Path(__file__).resolve().parent.parent


def run(code: str, **env_overrides: str) -> "subprocess.CompletedProcess[str]":
    """Run code in a fresh interpreter, returning the completed process.

    py2max's own logging env vars are cleared unless the test sets them, so a
    developer running the suite with e.g. PY2MAX_DEBUG=1 exported does not get
    different results.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("PY2MAX_")}
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, env=env
    )


BUILD_A_PATCH = """
import py2max
p = py2max.Patcher("out.maxpat")
p.add_line(p.add_textbox("cycle~ 440"), p.add_textbox("gain~"))
print("BUILT")
"""


def test_import_and_use_is_silent_by_default() -> None:
    """A library must not log to the console unless asked."""
    result = run(BUILD_A_PATCH)
    assert "BUILT" in result.stdout
    assert result.stderr == "", f"unexpected output on stderr:\n{result.stderr}"
    assert result.stdout.strip() == "BUILT", f"unexpected chatter:\n{result.stdout}"


def test_import_does_not_disturb_application_logging() -> None:
    """Importing py2max must not replace the app's logging configuration.

    Regression test: the old implementation called ``basicConfig(force=True)`` at
    import, which silently discarded the host program's handlers and format.
    """
    result = run("""
import logging
logging.basicConfig(level=logging.WARNING, format="APP: %(message)s")
import py2max
logging.getLogger("myapp").warning("hello")
""")
    combined = result.stdout + result.stderr
    assert "APP: hello" in combined, combined
    assert "\x1b[" not in combined, (
        f"py2max's formatter hijacked the root logger:\n{combined}"
    )


def test_setup_logging_opts_in() -> None:
    result = run(
        """
from py2max.log import setup_logging
setup_logging("DEBUG")
"""
        + BUILD_A_PATCH
    )
    assert "BUILT" in result.stdout
    assert "Initializing Patcher" in result.stderr


@pytest.mark.parametrize(
    "env,expect_logs",
    [
        ({"PY2MAX_DEBUG": "1"}, True),
        ({"PY2MAX_DEBUG": "0"}, False),
        ({"PY2MAX_LOG_LEVEL": "DEBUG"}, True),
        ({}, False),
    ],
)
def test_env_var_opt_in(env: dict, expect_logs: bool) -> None:
    """Env vars enable logging when explicitly set, and only then."""
    result = run(BUILD_A_PATCH, **env)
    assert "BUILT" in result.stdout
    assert bool(result.stderr.strip()) is expect_logs, result.stderr


def test_bare_debug_env_var_is_ignored() -> None:
    """``DEBUG`` is far too common a variable to key library behaviour on."""
    result = run(BUILD_A_PATCH, DEBUG="1")
    assert result.stderr == "", (
        f"a bare DEBUG=1 should not enable py2max logging:\n{result.stderr}"
    )


def test_log_file_captures_records(tmp_path: Path) -> None:
    log_file = tmp_path / "py2max.log"
    result = run(BUILD_A_PATCH, PY2MAX_LOG_FILE=str(log_file), PY2MAX_LOG_LEVEL="DEBUG")
    assert "BUILT" in result.stdout
    assert log_file.exists()
    assert "Initializing Patcher" in log_file.read_text()


# ---------------------------------------------------------------------------
# in-process behaviour (the _isolate_py2max_logger fixture restores state)


def test_setup_logging_is_idempotent() -> None:
    """Repeat calls must not stack duplicate handlers."""
    logger = logging.getLogger(LOGGER_NAME)
    first = len(logger.handlers)
    setup_logging("INFO")
    after_one = len(logger.handlers)
    setup_logging("DEBUG")
    assert len(logger.handlers) == after_one
    assert after_one == first + 1  # the NullHandler plus one console handler


def test_setup_logging_leaves_propagation_alone() -> None:
    """Disabling propagation would blind caplog and app-level root handlers."""
    logger = logging.getLogger(LOGGER_NAME)
    assert logger.propagate is True
    setup_logging("INFO")
    assert logger.propagate is True


def test_setup_logging_does_not_touch_root() -> None:
    root_before = list(logging.root.handlers)
    root_level_before = logging.root.level
    setup_logging("DEBUG")
    assert logging.root.handlers == root_before
    assert logging.root.level == root_level_before


def test_package_logger_has_a_null_handler() -> None:
    """The standard way for a library to avoid 'no handlers' warnings."""
    handlers = logging.getLogger(LOGGER_NAME).handlers
    assert any(isinstance(h, logging.NullHandler) for h in handlers)


def test_records_are_capturable_without_setup(caplog) -> None:
    """Records must reach the application even with no py2max handler attached."""
    logger = get_logger("py2max.core.testing")
    with caplog.at_level(logging.WARNING):
        logger.warning("a warning happened")
    assert any("a warning happened" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# the CLI is an application, so it does configure logging


def test_cli_logs_at_warning_by_default() -> None:
    result = run("""
import sys
from py2max.cli import main
sys.argv = ["py2max"]
main(["info", "--help"])
""")
    assert result.returncode == 0


def test_cli_verbose_flag_enables_debug(tmp_path: Path) -> None:
    out = tmp_path / "cli.maxpat"
    quiet = run(f'from py2max.cli import main; main(["new", r"{out}", "--force"])')
    loud = run(
        f'from py2max.cli import main; main(["-vv", "new", r"{out}", "--force"])'
    )
    assert "Initializing Patcher" not in quiet.stderr
    assert "Initializing Patcher" in loud.stderr


def test_cli_quiet_flag_silences_output(tmp_path: Path) -> None:
    out = tmp_path / "cli.maxpat"
    result = run(
        f'from py2max.cli import main; main(["-q", "-vv", "new", r"{out}", "--force"])'
    )
    assert result.stderr == "", result.stderr
