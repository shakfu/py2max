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


# --- install-folder overrides and user-level installs -------------------------


def test_override_accepts_macos_app_bundle(tmp_path, monkeypatch):
    app = tmp_path / "Max.app"
    refpages = app / "Contents" / "Resources" / "C74" / "docs" / "refpages"
    refpages.mkdir(parents=True)
    monkeypatch.setenv("PY2MAX_MAX_REFPAGES", str(app))
    assert parser.MaxRefCache()._get_refpages() == refpages


def test_override_accepts_windows_install_folder(tmp_path, monkeypatch):
    install = tmp_path / "Max 9"
    refpages = install / "resources" / "docs" / "refpages"
    refpages.mkdir(parents=True)
    monkeypatch.setenv("PY2MAX_MAX_REFPAGES", str(install))
    assert parser.MaxRefCache()._get_refpages() == refpages


def test_macos_discovery_searches_user_applications(tmp_path, monkeypatch):
    monkeypatch.delenv("PY2MAX_MAX_REFPAGES", raising=False)
    monkeypatch.setattr(parser.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(parser.Path, "home", classmethod(lambda cls: tmp_path))
    refpages = (
        tmp_path
        / "Applications"
        / "Max.app"
        / "Contents"
        / "Resources"
        / "C74"
        / "docs"
        / "refpages"
    )
    refpages.mkdir(parents=True)
    found = parser.MaxRefCache()._get_refpages()
    # a system-wide /Applications install, if any, is searched first
    assert found == refpages or str(found).startswith("/Applications")


# --- refpage structure ---------------------------------------------------------


def _cache_with(tmp_path, monkeypatch, name, xml):
    refpages = tmp_path / "refpages"
    (refpages / "max-ref").mkdir(parents=True)
    (refpages / "max-ref" / f"{name}.maxref.xml").write_text(xml)
    monkeypatch.setenv("PY2MAX_MAX_REFPAGES", str(refpages))
    return parser.MaxRefCache()


def test_non_refpage_xml_is_rejected(tmp_path, monkeypatch, caplog):
    cache = _cache_with(tmp_path, monkeypatch, "notref", "<html><body/></html>")
    assert cache.get_object_data("notref") is None
    assert "not a Max reference page" in caplog.text


def test_malformed_xml_is_rejected(tmp_path, monkeypatch):
    cache = _cache_with(tmp_path, monkeypatch, "broken", "<c74object name=")
    assert cache.get_object_data("broken") is None


def test_minimal_refpage_parses(tmp_path, monkeypatch):
    xml = '<c74object name="myobj"><digest>Does a thing</digest></c74object>'
    cache = _cache_with(tmp_path, monkeypatch, "myobj", xml)
    data = cache.get_object_data("myobj")
    assert data["name"] == "myobj" and data["digest"] == "Does a thing"
