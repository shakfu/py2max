"""
testing kwds_filter(kwds, **elems)

This can be useful if you want to keep the parameter in the methods's
signature but remove it the value is not used.

can improve documentation or be quite confusing.

"""


class BaseBox:
    """Base Max Box object"""

    def __init__(
        self,
        id: str,
        maxclass: str,
        numinlets: int,
        numoutlets: int,
        patching_rect: list[float],
        **kwds,
    ):
        self.id = id
        self.maxclass = maxclass
        self.numinlets = numinlets
        self.numoutlets = numoutlets
        self.patching_rect = patching_rect
        self._kwds = kwds


class Box(BaseBox):
    """Generic Max Box object"""

    def __init__(
        self,
        id: str,
        maxclass: str,
        numinlets: int,
        numoutlets: int,
        outlettype: list[str],
        patching_rect: list[float],
        **kwds,
    ):
        super().__init__(id, maxclass, numinlets, numoutlets, patching_rect, **kwds)
        self.outlettype = outlettype


def kwds_filter(kwds, **elems):
    """If any `elems` are not None updates `kwds` dict and returns it."""
    _dict = {k: elems[k] for k in elems if elems[k]}
    kwds.update(_dict)
    return kwds


class TextBox(Box):
    """Box with text"""

    def __init__(
        self,
        id: str,
        maxclass: str,
        text: str,
        numinlets: int,
        numoutlets: int,
        outlettype: list[str],
        patching_rect: list[float],
        varname: str = None,
        **kwds,
    ):
        super().__init__(
            id,
            maxclass,
            numinlets,
            numoutlets,
            outlettype,
            patching_rect,
            **kwds_filter(kwds, varname=varname),
        )
        self.text = text
        self._kwds = kwds


def f(x, y=None, **kwds):
    return (x, y, kwds)


def g(x, y=None, z=None, **kwds):
    if z:
        kwds["z"] = z
    return f(x, y, **kwds)


def eg_kwds_filter(x, y=None, z=None, **kwds):
    kwds = kwds_filter(kwds, z=z)
    return f(x, y, **kwds)


def test_t1_kwds_filter():
    assert eg_kwds_filter("a", 1) == ("a", 1, {})


def test_t2_kwds_filter():
    assert eg_kwds_filter("a", 1, z=10) == ("a", 1, {"z": 10})


def test_t3_kwds_filter():
    assert eg_kwds_filter("a", 1, z=None) == ("a", 1, {})


def test_t4_kwds_filter():
    assert eg_kwds_filter("a", 1, z=None, h=20) == ("a", 1, {"h": 20})


def test_t5_kwds_filter():
    assert eg_kwds_filter("a", 1, z=1, h=20) == ("a", 1, {"h": 20, "z": 1})
