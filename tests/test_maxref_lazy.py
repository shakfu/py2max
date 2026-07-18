"""Lazy bundle loading and thread safety for the maxref cache (REVIEW.md R5).

Bundle mode used to eagerly materialize every object into the cache on first
access, and the global cache had no locking. These tests force bundle mode by
stubbing out local-Max discovery.
"""

import threading

from py2max.maxref.parser import MaxRefCache


def _bundle_cache() -> MaxRefCache:
    c = MaxRefCache()
    c._get_refpages = lambda: None  # type: ignore[method-assign]  # force the shipped bundle
    return c


def test_bundle_is_not_eagerly_cached():
    c = _bundle_cache()
    names = c.refdict
    assert len(names) > 1000  # bundle loaded (name -> source map)
    assert len(c._cache) == 0  # ...but nothing materialized yet
    c.get_object_data("cycle~")
    assert set(c._cache) == {"cycle~"}  # only the requested object


def test_bundle_object_data_is_complete():
    c = _bundle_cache()
    d = c.get_object_data("cycle~")
    assert d is not None
    assert d["inlets"] and d["outlets"]


def test_concurrent_access_is_consistent():
    objs = ["cycle~", "gain~", "metro", "dac~", "umenu", "zl.stack"]
    ref = _bundle_cache()
    expected = {o: ref.get_object_data(o) for o in objs}

    c = _bundle_cache()  # fresh, unpopulated -> threads race to populate it
    errors: list[Exception] = []

    def worker() -> None:
        try:
            for o in objs:
                assert c.get_object_data(o) == expected[o]
        except Exception as e:  # pragma: no cover - only on a real race bug
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
