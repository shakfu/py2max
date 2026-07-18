"""R1: cross-platform Max refpages discovery.

Covers the ``PY2MAX_MAX_REFPAGES`` override (works on every OS, including Linux
and non-default install locations) and the Windows auto-discovery branch, which
previously did not exist -- non-macOS users were frozen to the shipped bundle.
"""

from py2max.maxref import parser


def _make_refpages(root):
    """Create a minimal refpages tree with one max-ref object and return it."""
    refpages = root / "refpages"
    max_ref = refpages / "max-ref"
    max_ref.mkdir(parents=True)
    # refdict only globs for the file; it is parsed lazily, so contents can be
    # a stub here.
    (max_ref / "myobj.maxref.xml").write_text("<c74object></c74object>")
    return refpages


# --- PY2MAX_MAX_REFPAGES override ------------------------------------------


def test_override_honored_when_dir_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("PY2MAX_MAX_REFPAGES", str(tmp_path))
    cache = parser.MaxRefCache()
    assert cache._get_refpages() == tmp_path


def test_override_ignored_when_dir_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("PY2MAX_MAX_REFPAGES", str(tmp_path / "does-not-exist"))
    # Simulate a no-Max platform so discovery can't pick up a real install.
    monkeypatch.setattr(parser.platform, "system", lambda: "Linux")
    cache = parser.MaxRefCache()
    assert cache._get_refpages() is None


def test_override_populates_refdict_across_platforms(tmp_path, monkeypatch):
    refpages = _make_refpages(tmp_path)
    monkeypatch.setenv("PY2MAX_MAX_REFPAGES", str(refpages))
    # The override must win regardless of host OS.
    monkeypatch.setattr(parser.platform, "system", lambda: "Linux")
    cache = parser.MaxRefCache()
    assert "myobj" in cache.refdict
    assert cache.category_map["myobj"] == "max"


# --- Windows discovery ------------------------------------------------------


def test_windows_discovery(tmp_path, monkeypatch):
    monkeypatch.delenv("PY2MAX_MAX_REFPAGES", raising=False)
    monkeypatch.setattr(parser.platform, "system", lambda: "Windows")

    prog = tmp_path / "ProgramFiles"
    refpages = prog / "Cycling '74" / "Max 8" / "resources" / "docs" / "refpages"
    refpages.mkdir(parents=True)
    monkeypatch.setenv("ProgramFiles", str(prog))
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)

    cache = parser.MaxRefCache()
    assert cache._get_refpages() == refpages


def test_windows_prefers_newest_max(tmp_path, monkeypatch):
    monkeypatch.delenv("PY2MAX_MAX_REFPAGES", raising=False)
    monkeypatch.setattr(parser.platform, "system", lambda: "Windows")

    base = tmp_path / "ProgramFiles" / "Cycling '74"
    for ver in ("Max 7", "Max 8", "Max 9"):
        (base / ver / "resources" / "docs" / "refpages").mkdir(parents=True)
    monkeypatch.setenv("ProgramFiles", str(tmp_path / "ProgramFiles"))
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)

    cache = parser.MaxRefCache()
    # sorted(reverse=True) picks the lexically-highest, i.e. the newest.
    assert cache._get_refpages().parents[2].name == "Max 9"


def test_unknown_platform_without_override_returns_none(monkeypatch):
    monkeypatch.delenv("PY2MAX_MAX_REFPAGES", raising=False)
    monkeypatch.setattr(parser.platform, "system", lambda: "Linux")
    cache = parser.MaxRefCache()
    assert cache._get_refpages() is None
