"""Shared pytest fixtures for the py2max test suite."""

import pytest


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Run each test in an isolated temporary working directory.

    Many tests write patches to a relative ``outputs/`` path. Without isolation
    those artifacts accumulate in the repo's ``outputs/`` directory and become
    shared mutable state across the suite. Changing into a fresh ``tmp_path``
    per test (with an ``outputs/`` subdirectory already created) makes those
    relative writes hermetic and self-cleaning, and removes the dependency on a
    pre-existing ``outputs/`` directory.

    Tests that read fixtures use paths anchored at ``__file__`` (e.g. a module
    ``DATA_DIR``), so they are unaffected by the working-directory change.
    """
    (tmp_path / "outputs").mkdir()
    monkeypatch.chdir(tmp_path)
