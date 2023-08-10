
from py2max.core import Rect


"""maxclassdb.py: meant to capture defaults related to a maxclass
"""

MAXCLASS_DEFAULTS = {
    "ezadc~": {
        "maxclass": "ezadc~",
        "numinlets": 1,
        "numoutlets": 2,
        "outlettype": ["signal", "signal"],
        "patching_rect": [0.0, 0.0, 45.0, 45.0],
    },
    "ezdac~": {
        "maxclass": "ezdac~",
        "numinlets": 2,
        "numoutlets": 0,
        "patching_rect": [0.1, 1.0, 45.0, 45.0],
    },
    "filtergraph~": {
        "fontface": 0,
        "linmarkers": [0.0, 11025.0, 16537.5],
        "logmarkers": [0.0, 100.0, 1000.0, 10000.0],
        "maxclass": "filtergraph~",
        "nfilters": 1,
        "numinlets": 8,
        "numoutlets": 7,
        "outlettype": ["list", "float", "float", "float", "float", "list", "int"],
        "parameter_enable": 0,
        "patching_rect": [1.0, 1.0, 256.0, 128.0],
        "setfilter": [0, 5, 1, 0, 0, 40.0, 1.0, 2.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    },
}



class Patcher:
    def __init__(self):
        self.rect = [85.0, 104.0, 640.0, 480.0]

    @property
    def width(self):
        return self.rect[2]

    @property
    def height(self):
        return self.rect[3]

class LayoutManager:
    """Utility class to help with object position calculations."""

    DEFAULT_PAD = 32.0
    DEFAULT_BOX_WIDTH = 66.0
    DEFAULT_BOX_HEIGHT = 22.0

    def __init__(self, parent: 'Patcher', pad: int = None,
                 box_width: int = None, box_height: int = None):
        self.parent = parent
        self.pad = pad or self.DEFAULT_PAD
        self.box_width = box_width or self.DEFAULT_BOX_WIDTH
        self.box_height = box_height or self.DEFAULT_BOX_HEIGHT
        self.x_layout_counter = 0
        self.y_layout_counter = 0
        self.prior_rect = None
        self.mclass_rect = None

    def get_rect_from_maxclass(self, maxclass):
        """retrieves default patching_rect from defaults dictionary."""
        try:
            rect = MAXCLASS_DEFAULTS[maxclass]['patching_rect']
            return Rect(*rect)
        except KeyError:
            return

    def get_absolute_pos(self, rect: Rect):
        """returns an absolute position for the object"""
        x, y, w, h = tuple(rect)

        pad = self.pad

        if x > 0.5 * self.parent.width:
            x1 = x - (w + pad)
            x = x1 - (x1 - self.parent.width) if x1 > self.parent.width else x1
        else:
            x1 = x + pad

        print('x1', x1)

        y1 = y - (h + pad)
        y = y1 - (y1 - self.parent.height) if y1 > self.parent.height else y1

        return [x, y, w, h]


    def get_relative_pos(self, rect: Rect):
        """returns a relative position for the object"""
        x, y, w, h = tuple(rect)

        pad = self.pad  # 32.0

        x_shift = 3 * pad * self.x_layout_counter
        y_shift = (1.5 * pad * self.y_layout_counter)
        x = pad + x_shift

        self.x_layout_counter += 1
        if x + w + 2 * pad > self.parent.width:
            self.x_layout_counter = 0
            self.y_layout_counter += 1

        y = pad + y_shift

        return [x, y, w, h]

    def get_pos(self, maxclass: str = None):
        """helper func providing very rough auto-layout of objects"""
        x = 0
        y = 0
        w = self.box_width   # 66.0
        h = self.box_height  # 22.0

        if maxclass:
            mclass_rect = self.get_rect_from_maxclass(maxclass)
            if mclass_rect and (mclass_rect.x or mclass_rect.y):
                if mclass_rect.x:
                    x = int(mclass_rect.x * self.parent.width)
                if mclass_rect.y:
                    y = int(mclass_rect.y * self.parent.height)

                _rect = Rect(x, y, mclass_rect.w, mclass_rect.h)
                return self.get_absolute_pos(_rect)

        _rect = Rect(x, y, w, h)
        return self.get_relative_pos(_rect)

    @property
    def patcher_rect(self):
        """return rect coordinates of the parent patcher"""
        return self.parent.rect

    def above(self, rect):
        """Return a position above the object"""
        x, y, w, h = rect
        return [x, y - self.box_height, w, h]

    def below(self, rect):
        """Return a position below the object"""
        x, y, w, h = rect
        return [x, y + (self.box_height + h), w, h]

    def left(self, rect):
        """Return a position left of the object"""
        x, y, w, h = rect
        return [x - self.box_width, y, w, h]

    def right(self, rect):
        """Return a position right of the object"""
        x, y, w, h = rect
        return [x + (self.box_width + w), y, w, h]



def test_layout():
    p = Patcher()
    m = LayoutManager(p)
    maxclasses = ['filtergraph~', 'ezdac~', 'ezadc~']
    # for _ in range(10):
    #     print(m.get_pos())
    print()
    print(m.parent.rect)
    for mc in maxclasses:
        print(m.get_pos(maxclass=mc), mc)


if __name__ == '__main__':
    test_layout()
