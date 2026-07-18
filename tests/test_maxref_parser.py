"""Regression tests for the maxref XML parser (REVIEW.md R3).

Two defects, both verified against the shipped Max reference data:

- Outlet ``<digest>`` extraction was asymmetric with inlets: it required the
  ``<outlet>`` element to have leading text and then stored that text instead
  of the digest, dropping ~2000 real outlet digests across ~1093 objects.
- A raw ``&`` in prose made the whole document non-well-formed, so the entire
  object was silently dropped on parse.

These tests use synthetic XML so they run without Max installed.
"""

from xml.etree import ElementTree

from py2max.maxref.parser import MaxRefCache, escape_bare_ampersands


def _extract(xml: str) -> dict:
    root = ElementTree.fromstring(xml)
    data: dict = {}
    MaxRefCache()._extract_inlets_outlets(root, data)
    return data


def test_outlet_digest_is_extracted():
    data = _extract(
        "<c74object name='x'>"
        "<inletlist><inlet id='0'><digest>in one</digest></inlet></inletlist>"
        "<outletlist><outlet id='0'><digest>out one</digest></outlet></outletlist>"
        "</c74object>"
    )
    assert data["inlets"][0]["digest"] == "in one"
    # Regression: the outlet digest used to be dropped.
    assert data["outlets"][0]["digest"] == "out one"


def test_outlet_without_digest_has_no_digest_key():
    data = _extract(
        "<c74object name='x'><outletlist><outlet id='0'/></outletlist></c74object>"
    )
    assert "digest" not in data["outlets"][0]


def test_clean_text_escapes_bare_ampersand():
    cache = MaxRefCache()
    cleaned = cache._clean_text(
        "<c74object name='x'><digest>attack & release</digest></c74object>"
    )
    root = ElementTree.fromstring(cleaned)  # must not raise
    assert root.find("digest").text.strip() == "attack & release"


def test_escape_bare_ampersands_preserves_valid_entities():
    assert escape_bare_ampersands("a & b") == "a &amp; b"
    assert escape_bare_ampersands("AT&T") == "AT&amp;T"
    # valid entities are left intact
    assert escape_bare_ampersands("a &amp; b") == "a &amp; b"
    assert escape_bare_ampersands("mu &#181; x") == "mu &#181; x"
    assert escape_bare_ampersands("q &quot; x") == "q &quot; x"
