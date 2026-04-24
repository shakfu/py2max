"""Test that the prebuilt maxref bundle covers no-Max environments (Linux)."""

from pathlib import Path

import pytest

from py2max.maxref import parser


BUNDLE_PATH = Path(parser.__file__).parent / "data" / "bundle.json.gz"


def _force_no_max(monkeypatch):
    """Make _get_refpages() return None to simulate Linux / no Max install."""
    monkeypatch.setattr(parser.MaxRefCache, "_get_refpages", lambda self: None)


def test_bundle_file_is_shipped():
    """Wheel must include the prebuilt bundle."""
    assert BUNDLE_PATH.exists(), (
        f"{BUNDLE_PATH.name} missing. Run scripts/build_maxref_bundle.py "
        "on a machine with Max installed."
    )
    # Non-trivial size: should be several hundred KB compressed.
    assert BUNDLE_PATH.stat().st_size > 100_000


def test_bundle_fallback_populates_refdict(monkeypatch):
    _force_no_max(monkeypatch)
    cache = parser.MaxRefCache()
    # Bundle should expose well over 500 objects.
    assert len(cache.refdict) > 500


def test_bundle_fallback_returns_object_data(monkeypatch):
    _force_no_max(monkeypatch)
    cache = parser.MaxRefCache()
    data = cache.get_object_data("cycle~")
    assert data is not None
    assert "inlets" in data
    assert "outlets" in data


def test_bundle_fallback_inlet_outlet_counts(monkeypatch):
    _force_no_max(monkeypatch)
    # Replace the module-level cache with a fresh bundle-backed one.
    monkeypatch.setattr(parser, "_maxref_cache", parser.MaxRefCache())

    # cycle~ has 2 inlets (frequency, phase) and 1 outlet.
    assert parser.get_inlet_count("cycle~") == 2
    assert parser.get_outlet_count("cycle~") == 1


def test_bundle_fallback_get_object_info(monkeypatch):
    _force_no_max(monkeypatch)
    monkeypatch.setattr(parser, "_maxref_cache", parser.MaxRefCache())

    info = parser.get_object_info("gain~")
    assert info is not None
    assert "inlets" in info


def test_bundle_fallback_preserves_categories(monkeypatch):
    _force_no_max(monkeypatch)
    cache = parser.MaxRefCache()
    # cycle~ is MSP; metro is Max.
    assert cache.category_map["cycle~"] == "msp"
    assert cache.category_map["metro"] == "max"


def test_bundle_unused_when_max_available():
    """With Max present the parser must NOT consult the bundle."""
    cache = parser.MaxRefCache()
    if cache._get_refpages() is None:
        pytest.skip("No local Max install; bundle fallback is the only path.")
    # refdict entries should be actual .maxref.xml files, not the sentinel.
    sample = next(iter(cache.refdict.values()))
    assert sample != parser._BUNDLE_SENTINEL
    assert str(sample).endswith(".maxref.xml")


def test_bundle_sentinel_cache_miss_returns_none(monkeypatch):
    """Defensive: a sentinel-path entry with a missing cache entry shouldn't
    crash by trying to read '<bundle>' as a file."""
    _force_no_max(monkeypatch)
    cache = parser.MaxRefCache()
    # Trigger refdict population first (which also pre-seeds cache), then
    # evict the cache entry to simulate a stale / reset scenario.
    _ = cache.refdict
    cache._cache.pop("cycle~", None)
    assert cache.get_object_data("cycle~") is None
