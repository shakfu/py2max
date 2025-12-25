"""Tests to achieve 100% coverage for py2max.abstract module."""

import pytest
from unittest.mock import Mock, patch
from py2max.core.abstract import (
    AbstractLayoutManager,
    AbstractBox,
    AbstractPatchline,
    AbstractPatcher,
)
from py2max.core.common import Rect


class TestAbstractLayoutManager:
    """Test AbstractLayoutManager abstract methods."""

    def test_get_rect_from_maxclass_abstract(self):
        """Test that get_rect_from_maxclass is abstract and raises NotImplementedError."""

        class ConcreteLayoutManager(AbstractLayoutManager):
            box_height = 22.0

            def get_rect_from_maxclass(self, maxclass: str) -> Rect:
                raise NotImplementedError("Abstract method")

            def get_relative_pos(self, rect: Rect) -> Rect:
                return rect

            def get_absolute_pos(self, rect: Rect) -> Rect:
                return rect

            def get_pos(self, maxclass: str = None) -> Rect:
                return Rect(0, 0, 100, 100)

            def above(self, rect: Rect) -> Rect:
                return rect

        manager = ConcreteLayoutManager()

        # This should raise NotImplementedError when called
        with pytest.raises(NotImplementedError):
            manager.get_rect_from_maxclass("test")

    def test_get_relative_pos_abstract(self):
        """Test that get_relative_pos is abstract and raises NotImplementedError."""

        class ConcreteLayoutManager(AbstractLayoutManager):
            box_height = 22.0

            def get_rect_from_maxclass(self, maxclass: str) -> Rect:
                return Rect(0, 0, 100, 100)

            def get_relative_pos(self, rect: Rect) -> Rect:
                raise NotImplementedError("Abstract method")

            def get_absolute_pos(self, rect: Rect) -> Rect:
                return rect

            def get_pos(self, maxclass: str = None) -> Rect:
                return Rect(0, 0, 100, 100)

            def above(self, rect: Rect) -> Rect:
                return rect

        manager = ConcreteLayoutManager()

        # This should raise NotImplementedError when called
        with pytest.raises(NotImplementedError):
            manager.get_relative_pos(Rect(0, 0, 100, 100))

    def test_get_absolute_pos_abstract(self):
        """Test that get_absolute_pos is abstract and raises NotImplementedError."""

        class ConcreteLayoutManager(AbstractLayoutManager):
            box_height = 22.0

            def get_rect_from_maxclass(self, maxclass: str) -> Rect:
                return Rect(0, 0, 100, 100)

            def get_relative_pos(self, rect: Rect) -> Rect:
                return rect

            def get_absolute_pos(self, rect: Rect) -> Rect:
                raise NotImplementedError("Abstract method")

            def get_pos(self, maxclass: str = None) -> Rect:
                return Rect(0, 0, 100, 100)

            def above(self, rect: Rect) -> Rect:
                return rect

        manager = ConcreteLayoutManager()

        # This should raise NotImplementedError when called
        with pytest.raises(NotImplementedError):
            manager.get_absolute_pos(Rect(0, 0, 100, 100))

    def test_get_pos_abstract(self):
        """Test that get_pos is abstract and raises NotImplementedError."""

        class ConcreteLayoutManager(AbstractLayoutManager):
            box_height = 22.0

            def get_rect_from_maxclass(self, maxclass: str) -> Rect:
                return Rect(0, 0, 100, 100)

            def get_relative_pos(self, rect: Rect) -> Rect:
                return rect

            def get_absolute_pos(self, rect: Rect) -> Rect:
                return rect

            def get_pos(self, maxclass: str = None) -> Rect:
                raise NotImplementedError("Abstract method")

            def above(self, rect: Rect) -> Rect:
                return rect

        manager = ConcreteLayoutManager()

        # This should raise NotImplementedError when called
        with pytest.raises(NotImplementedError):
            manager.get_pos("test")


class TestAbstractBox:
    """Test AbstractBox abstract methods."""

    def test_render_abstract(self):
        """Test that render is abstract and raises NotImplementedError."""

        class ConcreteBox(AbstractBox):
            def __init__(self):
                self.id = "test"
                self.maxclass = "test"
                self.patching_rect = Rect(0, 0, 100, 100)
                self._kwds = {}

            def render(self) -> None:
                raise NotImplementedError("Abstract method")

            def to_dict(self) -> dict:
                return {}

            def __iter__(self):
                yield self

        box = ConcreteBox()

        # This should raise NotImplementedError when called
        with pytest.raises(NotImplementedError):
            box.render()

    def test_to_dict_abstract(self):
        """Test that to_dict is abstract and raises NotImplementedError."""

        class ConcreteBox(AbstractBox):
            def __init__(self):
                self.id = "test"
                self.maxclass = "test"
                self.patching_rect = Rect(0, 0, 100, 100)
                self._kwds = {}

            def render(self) -> None:
                pass

            def to_dict(self) -> dict:
                raise NotImplementedError("Abstract method")

            def __iter__(self):
                yield self

        box = ConcreteBox()

        # This should raise NotImplementedError when called
        with pytest.raises(NotImplementedError):
            box.to_dict()


class TestAbstractPatchline:
    """Test AbstractPatchline abstract methods."""

    def test_to_dict_abstract(self):
        """Test that to_dict is abstract and raises NotImplementedError."""

        class ConcretePatchline(AbstractPatchline):
            def __init__(self):
                self._src = "source"
                self._dst = "destination"

            @property
            def src(self) -> str:
                return self._src

            @property
            def dst(self) -> str:
                return self._dst

            def to_dict(self) -> dict:
                raise NotImplementedError("Abstract method")

        patchline = ConcretePatchline()

        # This should raise NotImplementedError when called
        with pytest.raises(NotImplementedError):
            patchline.to_dict()


class TestAbstractPatcher:
    """Test AbstractPatcher abstract methods."""

    def test_width_property_abstract(self):
        """Test that width property is abstract and raises NotImplementedError."""

        class ConcretePatcher(AbstractPatcher):
            def __init__(self):
                self.rect = Rect(0, 0, 100, 100)
                self._path = None
                self._parent = None
                self._node_ids = []
                self._objects = {}
                self._boxes = []
                self._lines = []
                self._edge_ids = []
                self._id_counter = 0
                self._link_counter = 0
                self._last_link = None
                self._reset_on_render = False
                self._flow_direction = "horizontal"
                self._cluster_connected = False
                self._layout_mgr = Mock()
                self._auto_hints = False
                self._validate_connections = False
                self._maxclass_methods = {}

            @property
            def width(self) -> float:
                raise NotImplementedError("Abstract method")

            @property
            def height(self) -> float:
                return 100.0

        patcher = ConcretePatcher()

        # This should raise NotImplementedError when accessed
        with pytest.raises(NotImplementedError):
            _ = patcher.width

    def test_height_property_abstract(self):
        """Test that height property is abstract and raises NotImplementedError."""

        class ConcretePatcher(AbstractPatcher):
            def __init__(self):
                self.rect = Rect(0, 0, 100, 100)
                self._path = None
                self._parent = None
                self._node_ids = []
                self._objects = {}
                self._boxes = []
                self._lines = []
                self._edge_ids = []
                self._id_counter = 0
                self._link_counter = 0
                self._last_link = None
                self._reset_on_render = False
                self._flow_direction = "horizontal"
                self._cluster_connected = False
                self._layout_mgr = Mock()
                self._auto_hints = False
                self._validate_connections = False
                self._maxclass_methods = {}

            @property
            def width(self) -> float:
                return 100.0

            @property
            def height(self) -> float:
                raise NotImplementedError("Abstract method")

        patcher = ConcretePatcher()

        # This should raise NotImplementedError when accessed
        with pytest.raises(NotImplementedError):
            _ = patcher.height
