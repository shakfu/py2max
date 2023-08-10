"""
Tests building an object tree from a deeply nested structures
with recursive functions to visit each node.

"""

d = {
    'patcher': {
        'name': 'patcher',
        'boxes' : [
            {
                'box': {
                    'name': 'patcher.box[0]',
                    'text': 'ezdac~',
                    'maxclass': 'ezdac~',
                }
            },
            {
                'box': {
                    'name': 'patcher.box[1]',
                    'text': 'p subpatcher',
                    'maxclass': 'newobj',
                    'patcher': {
                        'name': 'patcher.box[1].patcher',
                        'boxes': [
                            {
                                'box': {
                                    'name': 'patcher.box[1].patcher.box[0]',
                                    'text': 'multislider',
                                    'maxclass': 'multislider',
                                }
                            },
                            {
                                'box': {
                                    'name': 'patcher.box[1].patcher.box[1]',
                                    'text': 'p subpatcher2',
                                    'maxclass': 'newobj',
                                    'patcher': {
                                        'name': 'patcher.box[1].patcher.box[0].patcher',
                                        'boxes': [
                                            {
                                                'box': {
                                                    'name': 'patcher.box[1].patcher.box[0].patcher.box[0]',
                                                    'text': 'playlist~',
                                                    'maxclass': 'playlist~',
                                                }
                                            }
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                }
            },
        ],
    }
}

class Object:
    name: str

    @classmethod
    def from_dict(cls, obj_dict):
        obj = cls()
        obj.__dict__.update(obj_dict)
        return obj
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"

class Patchline(Object):
    pass


class Box(Object):
    maxclass = 'newobj'
    def __init__(self):
        self.name = ''
        self._patcher = None

    def __iter__(self):
        yield self
        if self._patcher:
            yield from iter(self._patcher)

    @classmethod
    def from_dict(cls, obj_dict):
        box = cls()
        box.__dict__.update(obj_dict)
        if hasattr(box, 'patcher'):
            box._patcher = Patcher.from_dict(getattr(box, 'patcher'))
        return box


class EzDac(Box):
    maxclass = 'ezdac~'

class Multislider(Box):
    maxclass = 'multislider'

class PlayList(Box):
    maxclass = 'playlist~'

maxclasses = [EzDac, Multislider, PlayList]
db = {klass.maxclass: klass for klass in maxclasses}


class Patcher(Object):
    def __init__(self):
        self.name = ''
        self.boxes = []
        self.lines = []
        self._boxes = []
        self._lines = []

    def __iter__(self):
        yield self
        for box in self._boxes:
            yield from iter(box)

    @staticmethod
    def box_from_dict(d):
        if 'maxclass' in d:
            try:
                box_class = db[d['maxclass']]
            except KeyError:
                box_class = Box
            return box_class.from_dict(d)

    @classmethod
    def from_dict(cls, patcher_dict):
        """create a patcher instance from a dict"""

        patcher = cls()
        patcher.__dict__.update(patcher_dict)

        for box_dict in patcher.boxes:
            box = box_dict['box']
            b = patcher.box_from_dict(box)
            # b = Box.from_dict(box)
            patcher._boxes.append(b)

        for line_dict in patcher.lines:
            line = line_dict['patchline']
            pl = Patchline.from_dict(line)
            patcher._lines.append(pl)

        return patcher

def test_get_patchers():
    """get patchers recursively"""
    def walk(patcher, level=0):
        yield Patcher.from_dict(patcher)
        for box_dict in patcher['boxes']:
            box = box_dict['box']
            if 'patcher' in box:
                yield from walk(box['patcher'])
    root = d['patcher']
    nodes = list(walk(root))
    assert len(nodes) == 3

def test_visit_tree():
    """print names recursively"""
    def visit(node, func):
        patcher = node['patcher']
        func(patcher)
        for box_dict in patcher['boxes']:
            box = box_dict['box']
            func(box)
            if 'patcher' in box:
                visit(box, func)

    print_name = lambda node: print(node['name'])
    visit(d, print_name)

def test_object_builder():
    """build object tree recursively"""
    root = d['patcher']
    p = Patcher.from_dict(root)
    assert len(list(p)) == 8


